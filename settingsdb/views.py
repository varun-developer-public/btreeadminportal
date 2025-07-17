from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render, redirect
from .models import SourceOfJoining, PaymentAccount, TransactionLog
from .forms import SourceForm, PaymentAccountForm
import json

@staff_member_required
def settings_dashboard(request):
    return render(request, 'settingsdb/dashboard.html')

@staff_member_required
def source_list(request):
    sources = SourceOfJoining.objects.all()
    if request.method == 'POST':
        form = SourceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('source_list')
    else:
        form = SourceForm()
    return render(request, 'settingsdb/source_list.html', {'sources': sources, 'form': form})

@staff_member_required
def remove_source(request, pk):
    source = get_object_or_404(SourceOfJoining, pk=pk)
    source.delete()
    return redirect('source_list')

@staff_member_required
def payment_account_list(request):
    accounts = PaymentAccount.objects.all()
    if request.method == 'POST':
        form = PaymentAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payment_account_list')
    else:
        form = PaymentAccountForm()
    return render(request, 'settingsdb/payment_account_list.html', {'accounts': accounts, 'form': form})

@staff_member_required
def remove_payment_account(request, pk):
    account = get_object_or_404(PaymentAccount, pk=pk)
    account.delete()
    return redirect('payment_account_list')

def clean_transaction_data(details_json):
    try:
        raw_data = json.loads(details_json)
        cleaned_lines = []
        for field, value in raw_data.items():
            if field == 'csrfmiddlewaretoken':
                continue
            if isinstance(value, list):
                value = value[0]
            cleaned_lines.append(f"{field}: {value}")
        return "\n".join(cleaned_lines)
    except Exception as e:
        return f"Error parsing details: {e}"

@staff_member_required
def transaction_log(request):
    logs = TransactionLog.objects.select_related('user').order_by('-timestamp')
    for log in logs:
        log.cleaned_details = clean_transaction_data(log.changes)
    return render(request, 'settingsdb/transaction_log.html', {'logs': logs})
