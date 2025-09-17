import sys
import json
from datetime import datetime, date, time
from decimal import Decimal
from threading import local
from django.db.models import FileField
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

def serialize_model_instance(instance):
    """
    Serializes a model instance to a dictionary, handling relationships
    and prioritizing human-readable identifiers.
    """
    data = {}
    for field in instance._meta.get_fields(include_parents=False):
        # Skip reverse relations
        if not field.concrete and not field.is_relation:
            continue
        if field.one_to_many or (field.one_to_one and field.auto_created):
            continue

        field_name = field.name
        if hasattr(instance, field_name):
            if field.is_relation:
                related_obj = getattr(instance, field_name)
                if related_obj is None:
                    data[field_name] = None
                    continue
                
                # For ManyToMany, serialize as a list of strings
                if field.many_to_many:
                    data[field_name] = [str(obj) for obj in related_obj.all()]
                    continue

                # Prioritize human-readable fields on related objects
                if hasattr(related_obj, 'get_display_name'):
                    data[field_name] = related_obj.get_display_name()
                elif hasattr(related_obj, 'name'):
                    data[field_name] = related_obj.name
                elif hasattr(related_obj, 'course_name'):
                    data[field_name] = related_obj.course_name
                else:
                    data[field_name] = str(related_obj)

            else:
                value = getattr(instance, field_name)
                if isinstance(value, (datetime, date)):
                    data[field_name] = value.isoformat()
                elif isinstance(value, time):
                    data[field_name] = value.strftime('%H:%M:%S')
                elif isinstance(value, Decimal):
                    data[field_name] = float(value)
                elif isinstance(field, FileField):
                    if value and getattr(value, 'name', None):
                        try:
                            data[field_name] = value.url
                        except ValueError:
                            data[field_name] = None  # No file associated
                    else:
                        data[field_name] = None
                else:
                    data[field_name] = value
    return data


@receiver(pre_save)
def capture_old_instance(sender, instance, **kwargs):
    if is_running_migrations() or sender.__name__ == 'TransactionLog':
        return

    if not instance.pk:
        _old_instance_data.value = None
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
        _old_instance_data.value = serialize_model_instance(old_instance)
    except sender.DoesNotExist:
        _old_instance_data.value = None

@receiver(post_save)
def track_save(sender, instance, created, **kwargs):
    if is_running_migrations() or sender.__name__ == 'TransactionLog':
        return

    user = get_current_user()
    if user is None or not user.pk:
        return

    app_label = sender._meta.app_label
    new_data = serialize_model_instance(instance)
    old_data = getattr(_old_instance_data, 'value', None)

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
        
        changes = {'app': app_label, 'diff': diff, **new_data}
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
    data = serialize_model_instance(instance)
    changes = {'app': app_label, **data}

    TransactionLog.objects.create(
        user=user,
        table_name=sender.__name__,
        object_id=str(instance.pk),
        action='DELETE',
        changes=changes
    )
