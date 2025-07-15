import sys
import json
from datetime import datetime, date
from threading import local
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.apps import apps
from .models import TransactionLog

_user = local()
_old_instance_data = local()

def get_current_user():
    return getattr(_user, 'value', None)

def set_current_user(user):
    _user.value = user

def is_running_migrations():
    return 'makemigrations' in sys.argv or 'migrate' in sys.argv

def json_serializable(data):
    """Convert data dict values to JSON-serializable types, especially dates."""
    def serialize_value(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value
    return {k: serialize_value(v) for k, v in data.items()}

@receiver(pre_save)
def capture_old_instance(sender, instance, **kwargs):
    if is_running_migrations() or sender.__name__ == 'TransactionLog':
        return

    if not instance.pk:
        _old_instance_data.value = None
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
        _old_instance_data.value = model_to_dict(old_instance)
    except sender.DoesNotExist:
        _old_instance_data.value = None

@receiver(post_save)
def track_save(sender, instance, created, **kwargs):
    if is_running_migrations() or sender.__name__ == 'TransactionLog':
        return

    user = get_current_user()
    if user is None:
        return

    app_label = sender._meta.app_label
    new_data = model_to_dict(instance)
    new_data = json_serializable(new_data)

    old_data = getattr(_old_instance_data, 'value', None)
    if old_data:
        old_data = json_serializable(old_data)

    if created or not old_data:
        changes = {'app': app_label, **new_data}
        action = 'CREATE'
    else:
        diff = {}
        for key in new_data.keys():
            old_value = old_data.get(key)
            new_value = new_data.get(key)
            if old_value != new_value:
                diff[key] = {'old': old_value, 'new': new_value}
        changes = {'app': app_label, **diff}
        action = 'UPDATE'

    _old_instance_data.value = None

    TransactionLog.objects.create(
        user=user,
        table_name=sender.__name__,
        object_id=str(instance.pk),
        action=action,
        changes=changes
    )

@receiver(pre_delete)
def track_delete(sender, instance, **kwargs):
    if is_running_migrations() or sender.__name__ == 'TransactionLog':
        return

    user = get_current_user()
    if user is None:
        return

    app_label = sender._meta.app_label
    data = model_to_dict(instance)
    data = json_serializable(data)
    changes = {'app': app_label, **data}

    TransactionLog.objects.create(
        user=user,
        table_name=sender.__name__,
        object_id=str(instance.pk),
        action='DELETE',
        changes=changes
    )
