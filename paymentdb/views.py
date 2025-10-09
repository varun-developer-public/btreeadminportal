from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, F, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
import json
from datetime import datetime

from .models import Payment
from studentsdb.models import Student
from .forms import PaymentForm, PaymentUpdateForm

@login_required
def payment_list(request):
    user = request.user
    if hasattr(user, 'consultant_profile'):
        payments = Payment.objects.filter(student__consultant=user.consultant_profile.consultant).select_related('student', 'student__consultant').order_by('-id')
    else:
        payments = Payment.objects.select_related('student', 'student__consultant').order_by('-id')

    # Enhanced filtering logic
    search = request.GET.get('search', '').strip()
    emi_type = request.GET.get('emi_type', '').strip()
    payment_status = request.GET.get('payment_status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if search:
        payments = payments.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__consultant__name__icontains=search) |
            Q(payment_id__icontains=search)
        )

    if emi_type in ['NONE', '2', '3', '4']:
        payments = payments.filter(emi_type=emi_type)

    if payment_status:
        if payment_status == 'Pending':
            payments = payments.filter(total_pending_amount__gt=0)
        elif payment_status == 'Paid':
            payments = payments.filter(total_pending_amount__lte=0)

    filtered_pending_amount = 0
    # Filter by pending EMI date range if specified
    if date_from and date_to:
        pending_emi_query = Q()
        for i in range(1, 5):
            # An EMI is pending if its due date is in the range and it's not paid at all.
            is_pending_in_range = Q(
                **{f'emi_{i}_date__gte': date_from, f'emi_{i}_date__lte': date_to},
                **{f'emi_{i}_amount__isnull': False},
                **{f'emi_{i}_paid_amount__isnull': True}
            )
            pending_emi_query |= is_pending_in_range
        
        # Filter for payments that have a pending EMI in the date range and are currently pending.
        filtered_payments = payments.filter(pending_emi_query, total_pending_amount__gt=0).distinct()
        
        # Calculate the pending amount for the filtered date range
        for payment in filtered_payments:
            for i in range(1, 5):
                emi_date = getattr(payment, f'emi_{i}_date')
                if emi_date and date_from <= emi_date.strftime('%Y-%m-%d') <= date_to:
                    paid_amount = getattr(payment, f'emi_{i}_paid_amount')
                    if paid_amount is None:
                        emi_amount = getattr(payment, f'emi_{i}_amount') or 0
                        filtered_pending_amount += emi_amount

        payments = filtered_payments

    # Calculate total pending amount
    total_pending_amount = Payment.objects.filter(total_pending_amount__gt=0).aggregate(Sum('total_pending_amount'))['total_pending_amount__sum'] or 0

    # Process payments to include status
    processed_payments = []
    for payment in payments:
        payment.status = payment.get_payment_status()
        processed_payments.append(payment)

    paginator = Paginator(processed_payments, 10)  # Show 10 payments per page
    page = request.GET.get('page')

    try:
        payments_page = paginator.page(page)
    except PageNotAnInteger:
        payments_page = paginator.page(1)
    except EmptyPage:
        payments_page = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'payments': payments_page,
        'total_pending_amount': total_pending_amount,
        'filtered_pending_amount': filtered_pending_amount,
        'emi_types': Payment.EMI_CHOICES,
        'payment_statuses': [
            ('Pending', 'Pending'),
            ('Paid', 'Fully Paid'),
        ],
        'search': search,
        'emi_type': emi_type,
        'payment_status': payment_status,
        'date_from': date_from,
        'date_to': date_to,
        'query_params': query_params.urlencode(),
    }
    return render(request, 'paymentdb/payment_list.html', context)

@login_required
def payment_update(request, payment_id):
    payment = get_object_or_404(Payment, payment_id=payment_id)

    if request.method == 'POST':
        form = PaymentUpdateForm(request.POST, request.FILES, instance=payment)
        if form.is_valid():
            try:
                with transaction.atomic():
                    payment = form.save(commit=False)
                    for i in range(1, 5):
                        if f'emi_{i}_paid_amount' in form.changed_data:
                            setattr(payment, f'emi_{i}_updated_by', request.user)
                            break
                    payment.save()
                    # Find which EMI was just paid to show a nice message
                    for i in range(1, 5):
                        if f'emi_{i}_paid_amount' in form.changed_data:
                            paid_amount = form.cleaned_data.get(f'emi_{i}_paid_amount')
                            messages.success(request, f'EMI {i} payment of ₹{paid_amount} recorded successfully.')
                            break
                    return redirect('payment_list')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'An unexpected error occurred: {str(e)}')
    else:
        form = PaymentUpdateForm(instance=payment)

    total_pending = payment.calculate_total_pending()
    all_paid = total_pending == 0

    context = {
        'form': form,
        'payment': payment,
        'total_fees': payment.total_fees,
        'amount_paid': payment.amount_paid,
        'total_pending': total_pending,
        'total_paid': payment.total_fees - total_pending,
        'initial_payment_proof': payment.initial_payment_proof,
        'all_paid': all_paid,
    }
    return render(request, 'paymentdb/payment_update.html', context)

@login_required
def update_emi_date(request, payment_id):
    if request.method == 'POST':
        try:
            payment = get_object_or_404(Payment, payment_id=payment_id)
            data = json.loads(request.body)
            emi_field_name = data.get('emi_field')
            new_date_str = data.get('new_date')

            if not emi_field_name or not new_date_str:
                return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

            # Validate emi_field_name to prevent arbitrary attribute setting
            if not emi_field_name.startswith('emi_') or not emi_field_name.endswith('_date'):
                return JsonResponse({'status': 'error', 'message': 'Invalid EMI field'}, status=400)

            # Convert string to date object
            try:
                new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

            # Check if the EMI is already paid
            emi_number = emi_field_name.split('_')[1]
            paid_amount_field = f'emi_{emi_number}_paid_amount'
            if getattr(payment, paid_amount_field) is not None:
                return JsonResponse({'status': 'error', 'message': 'Cannot change the date of a paid EMI.'}, status=403)

            setattr(payment, emi_field_name, new_date)
            payment.save()

            return JsonResponse({'status': 'success', 'message': 'EMI date updated successfully.'})

        except Payment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Payment not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


def get_payment_details(request, student_id):
    try:
        student = Student.objects.get(student_id=student_id)
        payment = Payment.objects.get(student=student)
        
        emi_details = []
        if payment.emi_type != 'NONE':
            for i in range(1, int(payment.emi_type) + 1):
                emi_details.append({
                    'emi_number': i,
                    'due_amount': getattr(payment, f'emi_{i}_amount'),
                    'due_date': getattr(payment, f'emi_{i}_date'),
                    'paid_amount': getattr(payment, f'emi_{i}_paid_amount'),
                    'paid_date': getattr(payment, f'emi_{i}_paid_date'),
                })

        data = {
            'total_fees': payment.total_fees,
            'amount_paid': payment.amount_paid,
            'total_pending_amount': payment.total_pending_amount,
            'payment_status': payment.get_payment_status(),
            'emi_type': payment.emi_type,
            'emi_details': emi_details,
        }
        return JsonResponse(data)
    except (Student.DoesNotExist, Payment.DoesNotExist):
        return JsonResponse({'error': 'Payment details not found'}, status=404)
