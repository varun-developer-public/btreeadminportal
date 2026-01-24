from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, F, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
import json
from datetime import datetime
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Payment, PendingPaymentRecord
from studentsdb.models import Student
from .forms import PaymentForm, PaymentUpdateForm
from coursedb.models import Course

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
    student_status = request.GET.get('student_status', '').strip()
    course_status = request.GET.get('course_status', '').strip()

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
    if course_status:
        payments = payments.filter(student__course_status=course_status)
    if student_status:
        payments = payments.filter(**{f'student__{student_status}': True})

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
        'course_statuses': Student.COURSE_STATUS_CHOICES,
        'student_statuses': [
            ('mock_interview_completed', 'Mock Interview Completed'),
            ('placement_session_completed', 'Placement Session Completed'),
            ('certificate_issued', 'Certificate Issued'),
            ('onboardingcalldone', 'Onboarding Call Done'),
            ('interviewquestion_shared', 'Interview Question Shared'),
            ('resume_template_shared', 'Resume Template Shared'),
        ],
        'search': search,
        'emi_type': emi_type,
        'payment_status': payment_status,
        'course_status': course_status,
        'student_status': student_status,
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

class PendingPaymentsListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        u = self.request.user
        return (
            u.is_superuser
            or u.is_staff
            or getattr(u, 'role', None) in ('staff', 'batch_coordination')
        )

    def get(self, request):
        course_id = request.GET.get('course')
        batch_type = request.GET.get('batch_type')
        course_status = request.GET.get('course_status')
        per_page = int(request.GET.get('per_page', '10'))
        q = request.GET.get('q', '').strip()
        student_id = request.GET.get('student_id', '').strip()
        mobile = request.GET.get('mobile', '').strip()
        batch_code = request.GET.get('batch_code', '').strip()
        trainer = request.GET.get('trainer', '').strip()
        trainer_type = request.GET.get('trainer_type', '').strip()
        consultant = request.GET.get('consultant', '').strip()
        pending_min = request.GET.get('pending_min', '').strip()
        pending_max = request.GET.get('pending_max', '').strip()
        next_emi = request.GET.get('next_emi', '').strip()
        due_from = request.GET.get('due_from', '').strip()
        due_to = request.GET.get('due_to', '').strip()
        course_pct_min = request.GET.get('course_pct_min', '').strip()
        course_pct_max = request.GET.get('course_pct_max', '').strip()
        updated_by = request.GET.get('updated_by', '').strip()
        updated_from = request.GET.get('updated_from', '').strip()
        updated_to = request.GET.get('updated_to', '').strip()

        allowed_statuses = {'YTS', 'IP', 'H', 'D'}
        qs = (
            PendingPaymentRecord.objects
            .select_related('student', 'payment')
            .filter(status='Pending', course_status__in=allowed_statuses)
        )

        if course_id:
            try:
                qs = qs.filter(course_id=int(course_id))
            except ValueError:
                pass
        if course_status and course_status in allowed_statuses:
            qs = qs.filter(course_status=course_status)
        if batch_type:
            qs = qs.filter(batch_type=batch_type)
        if q:
            qs = qs.filter(
                Q(student_code__icontains=q) |
                Q(student_name__icontains=q) |
                Q(mobile__icontains=q) |
                Q(batch_code__icontains=q) |
                Q(course_name__icontains=q) |
                Q(trainer_name__icontains=q) |
                Q(consultant_name__icontains=q) |
                Q(feedback__icontains=q)
            )
        if student_id:
            qs = qs.filter(student_code__icontains=student_id)
        if mobile:
            qs = qs.filter(mobile__icontains=mobile)
        if batch_code:
            qs = qs.filter(batch_code__icontains=batch_code)
        if trainer:
            qs = qs.filter(trainer_name__icontains=trainer)
        if trainer_type in {'FT', 'FL'}:
            qs = qs.filter(trainer_type=trainer_type)
        if consultant:
            qs = qs.filter(consultant_name__icontains=consultant)
        if pending_min:
            try:
                qs = qs.filter(pending_amount__gte=float(pending_min))
            except ValueError:
                pass
        if pending_max:
            try:
                qs = qs.filter(pending_amount__lte=float(pending_max))
            except ValueError:
                pass
        if next_emi and next_emi in ['1', '2', '3', '4']:
            qs = qs.filter(next_emi_number=int(next_emi))
        if due_from:
            qs = qs.filter(next_due_date__gte=due_from)
        if due_to:
            qs = qs.filter(next_due_date__lte=due_to)
        if course_pct_min:
            try:
                qs = qs.filter(course_percentage__gte=float(course_pct_min))
            except ValueError:
                pass
        if course_pct_max:
            try:
                qs = qs.filter(course_percentage__lte=float(course_pct_max))
            except ValueError:
                pass
        if updated_by:
            qs = qs.filter(
                Q(edited_by__name__icontains=updated_by) |
                Q(edited_by__email__icontains=updated_by) |
                Q(edited_by__username__icontains=updated_by)
            )
        # Updated date range
        try:
            if updated_from:
                dt_from = datetime.strptime(updated_from, '%Y-%m-%d')
                qs = qs.filter(updated_at__gte=dt_from)
            if updated_to:
                dt_to = datetime.strptime(updated_to, '%Y-%m-%d')
                qs = qs.filter(updated_at__lte=dt_to)
        except ValueError:
            pass

        rows = []
        for rec in qs:
            student = rec.student
            rows.append({
                'record_id': rec.id,
                'student_pk': student.id if student else None,
                'student_id': rec.student_code,
                'student_name': rec.student_name,
                'mobile': rec.mobile,
                'batch_code': rec.batch_code,
                'batch_type': rec.batch_type,
                'course_name': rec.course_name,
                'course_status': rec.course_status,
                'total_fee': rec.total_fee,
                'amount_paid': rec.amount_paid,
                'pending_amount': rec.pending_amount,
                'next_emi_number': rec.next_emi_number,
                'next_emi_amount': rec.next_emi_amount,
                'next_due_date': rec.next_due_date,
                'consultant_name': rec.consultant_name,
                'trainer_name': rec.trainer_name,
                'trainer_type': rec.trainer_type,
                'course_percentage': rec.course_percentage,
                'feedback': rec.feedback,
                'updated_by_name': rec.edited_by.name if rec.edited_by else None,
                'updated_at': rec.updated_at,
            })

        rows.sort(key=lambda r: int(r['student_id'][3:]) if r['student_id'] and r['student_id'].startswith('BTR') else 0, reverse=True)

        paginator = Paginator(rows, per_page)
        page = request.GET.get('page')
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        query_params = request.GET.copy()
        if 'page' in query_params:
            del query_params['page']

        courses = Course.objects.all().order_by('course_name')
        batch_codes = list(
            PendingPaymentRecord.objects.filter(status='Pending')
            .exclude(batch_code__isnull=True)
            .exclude(batch_code='')
            .values_list('batch_code', flat=True)
            .distinct()
            .order_by('batch_code')
        )
        trainer_names = list(
            PendingPaymentRecord.objects.filter(status='Pending')
            .exclude(trainer_name__isnull=True)
            .exclude(trainer_name='')
            .values_list('trainer_name', flat=True)
            .distinct()
            .order_by('trainer_name')
        )
        consultant_names = list(
            PendingPaymentRecord.objects.filter(status='Pending')
            .exclude(consultant_name__isnull=True)
            .exclude(consultant_name='')
            .values_list('consultant_name', flat=True)
            .distinct()
            .order_by('consultant_name')
        )

        context = {
            'rows': page_obj,
            'courses': courses,
            'course_statuses': [('YTS', 'Yet to Start'), ('IP', 'In Progress'), ('D', 'Discontinued'), ('H', 'Hold')],
            'batch_types': [('WD', 'Weekday'), ('WE', 'Weekend'), ('WDWE', 'Weekday & Weekend'), ('Hybrid', 'Hybrid')],
            'per_page': per_page,
            'query_params': query_params.urlencode(),
            'q': q,
            'student_id': student_id,
            'mobile': mobile,
            'batch_code': batch_code,
            'trainer': trainer,
            'trainer_type': trainer_type,
            'consultant': consultant,
            'pending_min': pending_min,
            'pending_max': pending_max,
            'next_emi': next_emi,
            'due_from': due_from,
            'due_to': due_to,
            'course_pct_min': course_pct_min,
            'course_pct_max': course_pct_max,
            'batch_codes': batch_codes,
            'trainer_names': trainer_names,
            'consultant_names': consultant_names,
            'trainer_types': [('FT', 'Full Time'), ('FL', 'Freelancer')],
            'updated_by': updated_by,
            'updated_from': updated_from,
            'updated_to': updated_to,
        }
        return render(request, 'paymentdb/upcoming_payments_list.html', context)

@login_required
def update_pending_feedback(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    u = request.user
    if not (u.is_staff or u.is_superuser):
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
    rec = get_object_or_404(PendingPaymentRecord, pk=pk)
    feedback = request.POST.get('feedback', '').strip()
    rec.feedback = feedback
    rec.edited_by = u
    rec.save(update_fields=['feedback', 'edited_by', 'updated_at'])
    updated_by = getattr(u, 'name', None) or getattr(u, 'email', None) or u.get_username()
    return JsonResponse({
        'status': 'success',
        'updated_by': updated_by,
        'updated_at': rec.updated_at.strftime('%d %b %Y, %H:%M')
    })
