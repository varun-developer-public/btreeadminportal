from django.db import migrations

def add_dotnet_react_course(apps, schema_editor):
    CourseCategory = apps.get_model('studentsdb', 'CourseCategory')
    Course = apps.get_model('studentsdb', 'Course')

    category, _ = CourseCategory.objects.get_or_create(name="Programming Courses")
    
    Course.objects.get_or_create(
        code="C110",
        defaults={
            'name': "Dot Net+React",
            'category': category
        }
    )

class Migration(migrations.Migration):

    dependencies = [
        ('studentsdb', '0009_merge_20250719_1252'),
    ]

    operations = [
        migrations.RunPython(add_dotnet_react_course),
    ]