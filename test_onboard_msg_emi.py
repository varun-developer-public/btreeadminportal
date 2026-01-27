
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from studentsdb.models import Student, StudentConversation, ConversationMessage
from coursedb.models import Course, CourseCategory
from paymentdb.models import Payment
from settingsdb.signals import set_current_user

def test_onboard_message():
    User = get_user_model()
    
    # Create or get a user
    email = 'test_emi_user@example.com'
    if not User.objects.filter(email=email).exists():
        user = User.objects.create_user(email=email, name='Test EMI User', role='admin', password='password123')
    else:
        user = User.objects.get(email=email)
    
    # Set current user for signal
    set_current_user(user)
    
    # Create Course
    cat, _ = CourseCategory.objects.get_or_create(name='Test EMI Cat')
    course, _ = Course.objects.get_or_create(
        course_name='Test EMI Course',
        defaults={'category': cat, 'total_duration': 100, 'course_type': 'Course'}
    )
    
    # Create Student
    student = Student(
        first_name='TestStudent',
        last_name='EMI',
        email='teststudentemi@example.com',
        mode_of_class='ON',
        week_type='WD',
        course_id=course.id
    )
    student.save()
    
    # Create Payment
    # This should trigger the signal
    payment = Payment(
        student=student,
        total_fees=10000,
        amount_paid=1000,
        emi_type='3'
    )
    payment.save()
    
    # Check Conversation
    conv = StudentConversation.objects.filter(student=student).first()
    if not conv:
        print("Error: Conversation not created.")
        return
    
    # Check Message
    msg = ConversationMessage.objects.filter(conversation=conv).order_by('-created_at').first()
    if not msg:
        print("Error: No message created.")
        return
    
    print(f"Message Created: {msg.message}")
    
    expected_text_parts = [
        "I have onboarded the student today for the course Test EMI Course",
        "with 3 EMI split",
        "With name TestStudent EMI",
        "Student ID"
    ]
    
    all_present = True
    for part in expected_text_parts:
        if part not in msg.message:
            print(f"MISSING: {part}")
            all_present = False
            
    if all_present:
        print("SUCCESS: Message contains all expected parts.")
    else:
        print("FAILURE: Message content mismatch.")

    # Clean up
    payment.delete()
    student.delete()

if __name__ == '__main__':
    try:
        test_onboard_message()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
