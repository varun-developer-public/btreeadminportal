from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Batch, BatchStudent, BatchTransaction
from studentsdb.models import Student


def _get_user_from_instance(instance):
    """Helper to safely fetch user stored in instance._user"""
    return getattr(instance, "_user", None)


@receiver(post_save, sender=Batch)
def log_batch_save(sender, instance, created, **kwargs):
    """Log batch creation and updates automatically via signals"""
    user = _get_user_from_instance(instance)
    if not user:
        return  # Skip if no user context available

    transaction_type = "BATCH_CREATED" if created else "BATCH_UPDATED"

    details = {
        "batch_id": instance.batch_id,
        "course": str(instance.course) if instance.course else None,
        "trainer": str(instance.trainer) if instance.trainer else None,
        "start_date": str(instance.start_date) if instance.start_date else None,
        "end_date": str(instance.end_date) if instance.end_date else None,
        "batch_status": instance.get_batch_status_display(),
        "batch_type": instance.get_batch_type_display(),
    }

    BatchTransaction.log_transaction(
        batch=instance,
        transaction_type=transaction_type,
        user=user,
        details=details,
    )


@receiver(post_save, sender=BatchStudent)
def log_batch_student_save(sender, instance, created, **kwargs):
    """Log student addition to batch automatically via signals"""
    user = _get_user_from_instance(instance)
    if not user or not created:
        return

    details = {
        "student_id": instance.student.id,
        "student_name": str(instance.student),
        "activated_at": str(instance.activated_at) if instance.activated_at else None,
    }

    BatchTransaction.log_transaction(
        batch=instance.batch,
        transaction_type="STUDENT_ADDED",
        user=user,
        details=details,
        affected_students=[instance.student],
    )


@receiver(m2m_changed, sender=Batch.students.through)
def log_batch_students_changed(sender, instance, action, pk_set, **kwargs):
    """Log changes to the many-to-many relationship between Batch and Student"""
    if action not in ["post_add", "post_remove"]:
        return

    user = _get_user_from_instance(instance)
    if not user:
        return

    transaction_type = "STUDENT_ADDED" if action == "post_add" else "STUDENT_REMOVED"

    affected_students = list(Student.objects.filter(pk__in=pk_set))

    details = {
        "student_count": len(affected_students),
        "student_ids": list(pk_set),
        "student_names": [str(student) for student in affected_students],
    }

    BatchTransaction.log_transaction(
        batch=instance,
        transaction_type=transaction_type,
        user=user,
        details=details,
        affected_students=affected_students,
    )
