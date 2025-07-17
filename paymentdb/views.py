from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q

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
    emi_number = request.GET.get('emi_number', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if search:
        payments = payments.filter(
            Q(student__student_id__icontains=search) |
            Q(student__name__icontains=search) |
            Q(student__consultant__name__icontains=search) |
            Q(payment_id__icontains=search)
        )

    if emi_type in ['NONE', '2', '3', '4']:
        payments = payments.filter(emi_type=emi_type)

    # Filter by EMI date range if specified
    if emi_number and emi_number in ['1', '2', '3', '4']:
        date_field = f'emi_{emi_number}_date'
        if date_from:
            payments = payments.filter(**{f'{date_field}__gte': date_from})
        if date_to:
            payments = payments.filter(**{f'{date_field}__lte': date_to})

    # Process payments to include total pending amount
    processed_payments = []
    for payment in payments:
        payment.total_pending_amount = payment.calculate_total_pending()
        processed_payments.append(payment)

    # Filter by payment status if specified
    if payment_status:
        filtered_payments = []
        for payment in processed_payments:
            if payment_status == 'PAID' and payment.total_pending_amount == 0:
                filtered_payments.append(payment)
            elif payment_status == 'PARTIAL' and 0 < payment.total_pending_amount < payment.total_fees:
                filtered_payments.append(payment)
            elif payment_status == 'PENDING' and payment.total_pending_amount == payment.total_fees:
                filtered_payments.append(payment)
        processed_payments = filtered_payments

    context = {
        'payments': processed_payments,
        'emi_types': Payment.EMI_CHOICES,
        'payment_statuses': [
            ('PENDING', 'Pending'),
            ('PARTIAL', 'Partially Paid'),
            ('PAID', 'Fully Paid'),
        ],
        'emi_numbers': [
            ('1', 'EMI 1'),
            ('2', 'EMI 2'),
            ('3', 'EMI 3'),
            ('4', 'EMI 4'),
        ],
        'search': search,
        'emi_type': emi_type,
        'payment_status': payment_status,
        'emi_number': emi_number,
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
            except Exception as e:
                messages.error(request, f'Error updating payment: {str(e)}')
    else:
        form = PaymentUpdateForm(instance=payment)

    context = {
        'form': form,
        'payment': payment,
        'total_fees': payment.total_fees,
        'amount_paid': payment.amount_paid,
        'total_pending': payment.calculate_total_pending(),
        'initial_payment_proof': payment.initial_payment_proof
    }
    return render(request, 'paymentdb/payment_update.html', context)
