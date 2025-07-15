from django.shortcuts import render, get_object_or_404
from .models import Payment
from studentsdb.models import Student
from django.contrib.auth.decorators import login_required

@login_required
def payment_list(request):
    payments = Payment.objects.select_related('student').all()
    return render(request, 'paymentdb/payment_list.html', {'payments': payments})

@login_required
def payment_detail(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    payment = Payment.objects.filter(student=student).first()
    context = {
        'student': student,
        'payment': payment,
    }
    return render(request, 'paymentdb/payment_detail.html', context)
