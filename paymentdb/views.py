from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, F
from django.http import JsonResponse
import json
from datetime import datetime

from .models import Payment
from studentsdb.models import Student
from .forms import PaymentForm, PaymentUpdateForm

@login_required
def payment_list(request):
    payments = Payment.objects.select_related('student', 'student__consultant')

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

    # Filter by pending EMI date range if specified
    if date_from and date_to:
        pending_emi_query = Q()
        for i in range(1, 5):
            # An EMI is pending if its due date is in the range and it's not fully paid.
            is_pending_in_range = Q(
                **{f'emi_{i}_date__gte': date_from, f'emi_{i}_date__lte': date_to},
                **{f'emi_{i}_amount__isnull': False}
            ) & (
                Q(**{f'emi_{i}_paid_amount__isnull': True}) | Q(**{f'emi_{i}_paid_amount__lt': F(f'emi_{i}_amount')})
            )
            pending_emi_query |= is_pending_in_range
        payments = payments.filter(pending_emi_query).distinct()

    # Process payments to include total pending amount and status
    processed_payments = []
    for payment in payments:
        payment.total_pending_amount = payment.calculate_total_pending()
        payment.total_paid = payment.total_fees - payment.total_pending_amount
        if payment.total_pending_amount <= 0:
            payment.status = 'PAID'
        elif payment.total_pending_amount >= payment.total_fees:
            payment.status = 'PENDING'
        else:
            payment.status = 'PARTIAL'
        processed_payments.append(payment)

    # Filter by payment status if specified
    if payment_status:
        # This filtering should happen on the processed list
        processed_payments = [p for p in processed_payments if p.status == payment_status]

    context = {
        'payments': processed_payments,
        'emi_types': Payment.EMI_CHOICES,
        'payment_statuses': [
            ('PENDING', 'Pending'),
            ('PARTIAL', 'Partially Paid'),
            ('PAID', 'Fully Paid'),
        ],
        'search': search,
        'emi_type': emi_type,
        'payment_status': payment_status,
        'date_from': date_from,
        'date_to': date_to,
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
                    form.save()
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
