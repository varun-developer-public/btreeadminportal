from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Batch, BatchStudent, BatchTransaction


@receiver(post_save, sender=Batch)
def log_batch_save(sender, instance, created, **kwargs):
    """Log batch creation and updates automatically via signals"""
    # Skip if the save was triggered by the transaction logging itself
    if kwargs.get('skip_transaction_logging', False):
        return
    
    # Get the user from kwargs if available
    user = kwargs.get('user', None)
    if not user and hasattr(instance, '_user'):
        user = getattr(instance, '_user', None)
    
    if not user:
        return  # Skip logging if no user is available
    
    transaction_type = 'BATCH_CREATED' if created else 'BATCH_UPDATED'
    
    # Prepare transaction details
    details = {
        'batch_id': instance.batch_id,
        'course': str(instance.course) if instance.course else None,
        'trainer': str(instance.trainer) if instance.trainer else None,
        'start_date': str(instance.start_date) if instance.start_date else None,
        'end_date': str(instance.end_date) if instance.end_date else None,
        'batch_status': instance.batch_status,
        'batch_type': instance.batch_type
    }
    
    # Log the transaction
    BatchTransaction.log_transaction(
        batch=instance,
        transaction_type=transaction_type,
        user=user,
        details=details
    )


@receiver(post_save, sender=BatchStudent)
def log_batch_student_save(sender, instance, created, **kwargs):
    """Log student addition to batch automatically via signals"""
    # Skip if the save was triggered by the transaction logging itself
    if kwargs.get('skip_transaction_logging', False):
        return
    
    # Only log when a student is first added to a batch
    if not created:
        return
    
    # Get the user from kwargs if available
    user = kwargs.get('user', None)
    if not user and hasattr(instance, '_user'):
        user = getattr(instance, '_user', None)
    
    if not user:
        return  # Skip logging if no user is available
    
    # Prepare transaction details
    details = {
        'student_id': instance.student.id,
        'student_name': str(instance.student),
        'activated_at': str(instance.activated_at) if instance.activated_at else None
    }
    
    # Log the transaction
    BatchTransaction.log_transaction(
        batch=instance.batch,
        transaction_type='STUDENT_ADDED',
        user=user,
        details=details,
        affected_students=[instance.student]
    )


@receiver(m2m_changed, sender=Batch.students.through)
def log_batch_students_changed(sender, instance, action, pk_set, **kwargs):
    """Log changes to the many-to-many relationship between Batch and Student"""
    # Skip if the save was triggered by the transaction logging itself
    if kwargs.get('skip_transaction_logging', False):
        return
    
    # Only process post actions
    if action not in ['post_add', 'post_remove']:
        return
    
    # Get the user from kwargs if available
    user = kwargs.get('user', None)
    if not user and hasattr(instance, '_user'):
        user = getattr(instance, '_user', None)
    
    if not user:
        return  # Skip logging if no user is available
    
    from .models import Student  # Import here to avoid circular imports
    
    # Determine transaction type based on action
    transaction_type = 'STUDENT_ADDED' if action == 'post_add' else 'STUDENT_REMOVED'
    
    # Get affected students
    affected_students = list(Student.objects.filter(pk__in=pk_set))
    
    # Prepare transaction details
    details = {
        'student_count': len(affected_students),
        'student_ids': list(pk_set),
        'student_names': [str(student) for student in affected_students]
    }
    
    # Log the transaction
    BatchTransaction.log_transaction(
        batch=instance,
        transaction_type=transaction_type,
        user=user,
        details=details,
        affected_students=affected_students
    )