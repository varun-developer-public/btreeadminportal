from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

class CourseCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Course Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            last_category = CourseCategory.objects.order_by('id').last()
            if last_category:
                last_id = int(last_category.code[1:])
                self.code = 'C' + str(last_id + 1)
            else:
                self.code = 'C1'
        super().save(*args, **kwargs)

class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('Course', 'Course'),
        ('Module', 'Module'),
    ]

    course_name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True, blank=True)
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES, default='Course')
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, related_name='courses')
    total_duration = models.DecimalField(
        max_digits=8,        
        decimal_places=2,   
        help_text="Duration in hours",
        blank=False,
        null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.course_name

    def save(self, *args, **kwargs):
        if not self.code:
            last_course = Course.objects.filter(category=self.category).order_by('id').last()
            category_code = self.category.code
            if last_course:
                last_id = int(last_course.code[len(category_code):])
                new_id = last_id + 1
            else:
                new_id = 1
            self.code = f"{category_code}{new_id:03d}" 
        super().save(*args, **kwargs)

class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=255)
    module_duration = models.DecimalField(
        max_digits=8,        
        decimal_places=2,   
        validators=[MinValueValidator(0.5)],
        help_text="Duration in hours"
    )
    has_topics = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.course.course_name})"

class Topic(models.Model):
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=255)
    topic_duration = models.DecimalField(
        max_digits=8,        
        decimal_places=2,   
        validators=[MinValueValidator(0.5)],
        help_text="Duration in hours"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
