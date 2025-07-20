from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Consultant

User = get_user_model()

@receiver(post_save, sender=User)
def sync_user_email_to_consultant(sender, instance, **kwargs):
    if hasattr(instance, 'consultant_profile'):
        consultant = instance.consultant_profile.consultant
        if consultant.email != instance.email:
            consultant.email = instance.email
            consultant.save()

@receiver(post_save, sender=Consultant)
def sync_consultant_email_to_user(sender, instance, **kwargs):
    try:
        user = User.objects.get(consultant_profile__consultant=instance)
        if user.email != instance.email:
            user.email = instance.email
            user.save()
    except User.DoesNotExist:
        pass