from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'student', 'payment_account', 'total_fees', 'amount_paid', 'total_pending_amount', 'emi_type')
    search_fields = ('payment_id', 'student__student_id', 'student__first_name', 'student__last_name')
    list_filter = ('emi_type', 'payment_account')
    readonly_fields = ('payment_id', 'total_pending_amount')
    fields = (
        'payment_id', 'student', 'payment_account', 'total_fees', 'gst_bill', 'amount_paid', 'emi_type',
        'initial_payment_proof',
        'emi_1_amount', 'emi_1_date', 'emi_1_paid_amount', 'emi_1_paid_date', 'emi_1_proof', 'emi_1_updated_by',
        'emi_2_amount', 'emi_2_date', 'emi_2_paid_amount', 'emi_2_paid_date', 'emi_2_proof', 'emi_2_updated_by',
        'emi_3_amount', 'emi_3_date', 'emi_3_paid_amount', 'emi_3_paid_date', 'emi_3_proof', 'emi_3_updated_by',
        'emi_4_amount', 'emi_4_date', 'emi_4_paid_amount', 'emi_4_paid_date', 'emi_4_proof', 'emi_4_updated_by',
        'total_pending_amount'
    )
