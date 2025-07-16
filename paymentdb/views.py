from django.shortcuts import get_object_or_404, render, redirect
from .models import Payment
from studentsdb.models import Student
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .forms import PaymentUpdateForm
from django.db import transaction

@login_required
def payment_list(request):
    payments = Payment.objects.select_related('student', 'student__consultant').all()

    search = request.GET.get('search', '').strip()  # For student id, name, or consultant
    emi_type = request.GET.get('emi_type', '').strip()
    emi_field = request.GET.get('emi_field', '').strip()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if search:
        payments = payments.filter(
            Q(student__student_id__icontains=search) |
            Q(student__name__icontains=search) |
            Q(student__consultant__name__icontains=search)
        )

    if emi_type in ['NONE', '2', '3', '4']:
        payments = payments.filter(emi_type=emi_type)

    valid_emi_fields = ['emi_1_date', 'emi_2_date', 'emi_3_date', 'emi_4_date']
    if emi_field in valid_emi_fields:
        if start_date and end_date:
            payments = payments.filter(**{f"{emi_field}__range": [start_date, end_date]})
        elif start_date:
            payments = payments.filter(**{f"{emi_field}__gte": start_date})
        elif end_date:
            payments = payments.filter(**{f"{emi_field}__lte": end_date})

    payments = payments.order_by('student__student_id')

    context = {
        'payments': payments,
        'request': request,
    }
    return render(request, 'paymentdb/payment_list.html', context)

@login_required
def payment_detail(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    payment = Payment.objects.filter(student=student).first()
    context = {
        'student': student,
        'payment': payment,
    }
    return render(request, 'paymentdb/payment_detail.html', context)



@login_required
def payment_update(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    def get_editable_emi(payment):
        # First EMI amount exists but no proof => editable EMI
        for i in range(1, 5):
            amount = getattr(payment, f"emi_{i}_amount")
            proof = getattr(payment, f"emi_{i}_proof")
            if amount and not proof:
                return i
        return None

    editable_index = get_editable_emi(payment)

    if request.method == 'POST':
        form = PaymentUpdateForm(request.POST, request.FILES, instance=payment)

        if form.is_valid() and editable_index:
            # Fetch fresh from DB for original EMI amounts before update
            original_payment = payment.__class__.objects.get(pk=payment.pk)
            emi_amount = getattr(original_payment, f"emi_{editable_index}_amount") or 0

            paid = form.cleaned_data.get(f"emi_{editable_index}_paid") or 0

            # Validate paid <= emi_amount
            if paid > emi_amount:
                form.add_error(f"emi_{editable_index}_paid", "Paid amount cannot exceed EMI amount.")
            else:
                with transaction.atomic():
                    # Update current EMI amount to paid amount
                    setattr(payment, f"emi_{editable_index}_amount", paid)

                    balance = emi_amount - paid

                    # Carry forward unpaid balance to next EMI if any
                    if balance > 0 and editable_index < 4:
                        next_emi_field = f"emi_{editable_index + 1}_amount"
                        next_emi_val = getattr(payment, next_emi_field) or 0
                        setattr(payment, next_emi_field, next_emi_val + balance)

                    # Save proof if uploaded
                    proof = form.cleaned_data.get(f"emi_{editable_index}_proof")
                    if proof:
                        setattr(payment, f"emi_{editable_index}_proof", proof)

                    # Paid date update only if field enabled (normally disabled)
                    paid_date = form.cleaned_data.get(f"emi_{editable_index}_date")
                    if paid_date and not form.fields[f'emi_{editable_index}_date'].disabled:
                        setattr(payment, f"emi_{editable_index}_date", paid_date)

                    # Recalculate total paid & pending
                    total_paid = payment.amount_paid + sum(
                        getattr(payment, f"emi_{i}_amount") or 0 for i in range(1, 5)
                    )
                    payment.total_pending_amount = payment.total_fees - total_paid

                    payment.save()

                return redirect('payment_list')

    else:
        form = PaymentUpdateForm(instance=payment)

    emi_fields = []
    for i in range(1, 5):
        proof_file = getattr(payment, f'emi_{i}_proof')
        proof_url = proof_file.url if proof_file else None

        emi_fields.append({
            'label': f'EMI {i}',
            'amount': form[f'emi_{i}_amount'],
            'date': form[f'emi_{i}_date'],
            'paid': form[f'emi_{i}_paid'],
            'proof': form[f'emi_{i}_proof'],
            'proof_url': proof_url,
            'editable': (i == editable_index)
        })

    return render(request, 'paymentdb/payment_update.html', {
        'form': form,
        'payment': payment,
        'emi_fields': emi_fields,
    })
