from django.db import migrations

def update_course_names(apps, schema_editor):
    Course = apps.get_model('studentsdb', 'Course')
    
    name_updates = {
        "AWS Data Engg": "AWS Data Engineering",
        "Azure Data Engg": "Azure Data Engineering",
        "Business Analyst": "Bussiness Analyst",
        "Teraform": "Terraform",
        "Android Devlopment": "Android development",
        "Saleforce": "Salesforce",
        "Python Full Stack": "Python FSD",
        "Java Full Stack": "Java FSD",
        "UI UX": "UIUX",
        "Cyber Security": "Cyber security",
        "MERN Stack": "Mern Stack",
        "Java Advanced": "Advance Java",
    }

    for old_name, new_name in name_updates.items():
        try:
            course = Course.objects.get(name=old_name)
            course.name = new_name
            course.save()
        except Course.DoesNotExist:
            pass

class Migration(migrations.Migration):

    dependencies = [
        ('studentsdb', '0006_alter_student_email_alter_student_enrollment_date'),
    ]

    operations = [
        migrations.RunPython(update_course_names),
    ]