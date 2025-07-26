import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from coursedb.models import CourseCategory, Course

def generate_category_codes():
    categories = CourseCategory.objects.all().order_by('id')
    for i, category in enumerate(categories):
        category.code = f"C{i+1}"
        category.save()

def generate_course_codes():
    courses = Course.objects.all().order_by('category__id', 'id')
    category_counts = {}
    for course in courses:
        category_code = course.category.code
        if category_code not in category_counts:
            category_counts[category_code] = 1
        else:
            category_counts[category_code] += 1
        
        course.code = f"{category_code}{category_counts[category_code]:03d}"
        course.save()

if __name__ == "__main__":
    generate_category_codes()
    generate_course_codes()
    print("Codes generated successfully.")