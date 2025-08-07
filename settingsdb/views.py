from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render, redirect
from .models import SourceOfJoining, PaymentAccount, TransactionLog
from .forms import SourceForm, PaymentAccountForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
from django.http import HttpResponse
from io import BytesIO

from studentsdb.models import Student, Course, CourseCategory
from trainersdb.models import Trainer
from consultantdb.models import Consultant
from batchdb.models import Batch
from paymentdb.models import Payment
from placementdb.models import Placement, CompanyInterview
from placementdrive.models import PlacementDrive
from accounts.models import CustomUser
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
    log_list = TransactionLog.objects.select_related('user').order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(log_list, 20)  # Show 20 logs per page
    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    for log in logs:
        log.cleaned_details = clean_transaction_data(log.changes)
        
    return render(request, 'settingsdb/transaction_log.html', {'logs': logs})

@staff_member_required
def export_data(request):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        models_to_export = {
            'Students': Student,
            'Courses': Course,
            'CourseCategories': CourseCategory,
            'Trainers': Trainer,
            'Consultants': Consultant,
            'Batches': Batch,
            'Payments': Payment,
            'Placements': Placement,
            'CompanyInterviews': CompanyInterview,
            'PlacementDrives': PlacementDrive,
            'Users': CustomUser,
            'SourceOfJoining': SourceOfJoining,
            'PaymentAccounts': PaymentAccount,
        }

        for sheet_name, model in models_to_export.items():
            data = list(model.objects.all().values())
            df = pd.DataFrame(data)
            
            # Convert datetime columns to timezone-unaware
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.tz_localize(None)
            
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="backup_data.xlsx"'
    return response

from django.db import transaction

@staff_member_required
def import_data(request):
    if request.method == 'POST':
        excel_file = request.FILES['excel_file']
        xls = pd.ExcelFile(excel_file)
        
        with transaction.atomic():
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name).replace({pd.NaT: None, float('nan'): None})
                model = None
                if sheet_name == 'Students': model = Student
                elif sheet_name == 'Courses': model = Course
                elif sheet_name == 'CourseCategories': model = CourseCategory
                elif sheet_name == 'Trainers': model = Trainer
                elif sheet_name == 'Consultants': model = Consultant
                elif sheet_name == 'Batches': model = Batch
                elif sheet_name == 'Payments': model = Payment
                elif sheet_name == 'Placements': model = Placement
                elif sheet_name == 'CompanyInterviews': model = CompanyInterview
                elif sheet_name == 'PlacementDrives': model = PlacementDrive
                elif sheet_name == 'Users': model = CustomUser
                elif sheet_name == 'SourceOfJoining': model = SourceOfJoining
                elif sheet_name == 'PaymentAccounts': model = PaymentAccount

                if model:
                    for _, row in df.iterrows():
                        model.objects.update_or_create(id=row['id'], defaults=row.to_dict())

        return redirect('settings_dashboard')
    return render(request, 'settingsdb/import_data.html')
