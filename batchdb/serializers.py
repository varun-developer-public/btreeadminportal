from rest_framework import serializers
from django.db.models import Q
from .models import Batch, BatchStudent, TransferRequest, BatchTransaction, TrainerHandover
from coursedb.models import Course, CourseCategory
from trainersdb.models import Trainer
from studentsdb.models import Student
from django.contrib.auth import get_user_model

User = get_user_model()

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = '__all__'

class BatchStudentSerializer(serializers.ModelSerializer):
    student_name = serializers.StringRelatedField(source='student', read_only=True)
    batch_id = serializers.StringRelatedField(source='batch', read_only=True)
    
    class Meta:
        model = BatchStudent
        fields = ['id', 'batch', 'batch_id', 'student', 'student_name', 'is_active', 'activated_at', 'deactivated_at']
        read_only_fields = ['activated_at', 'deactivated_at']


class BatchSerializer(serializers.ModelSerializer):
    course_name = serializers.StringRelatedField(source='course', read_only=True)
    trainer_name = serializers.StringRelatedField(source='trainer', read_only=True)
    batch_type_display = serializers.CharField(source='get_batch_type_display', read_only=True)
    batch_status_display = serializers.CharField(source='get_batch_status_display', read_only=True)
    slot_time = serializers.CharField(source='get_slottime', read_only=True)
    active_students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Batch
        fields = [
            'id', 'batch_id', 'course', 'course_name', 'trainer', 'trainer_name',
            'start_date', 'end_date', 'batch_type', 'batch_type_display',
            'batch_status', 'batch_status_display', 'start_time', 'end_time',
            'days', 'hours_per_day', 'batch_percentage',
            'slot_time', 'active_students_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['batch_id', 'created_at', 'updated_at']
    
    def get_active_students_count(self, obj):
        return obj.batchstudent_set.filter(is_active=True).count()
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        
        # Pass user to save method for transaction logging
        batch = Batch.objects.create(**validated_data)
        batch.save(user=user)
        return batch
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['updated_by'] = user
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Pass user to save method for transaction logging
        instance.save(user=user)
        return instance


class BatchDetailSerializer(BatchSerializer):
    active_students = serializers.SerializerMethodField()
    
    class Meta(BatchSerializer.Meta):
        fields = BatchSerializer.Meta.fields + ['active_students']
    
    def get_active_students(self, obj):
        active_batch_students = obj.batchstudent_set.filter(is_active=True)
        return BatchStudentSerializer(active_batch_students, many=True).data


class TransferRequestSerializer(serializers.ModelSerializer):
    from_batch_id = serializers.StringRelatedField(source='from_batch', read_only=True)
    from_batch_code = serializers.StringRelatedField(source='from_batch.batch_id', read_only=True)
    to_batch_id = serializers.StringRelatedField(source='to_batch', read_only=True)
    to_batch_code = serializers.StringRelatedField(source='to_batch.batch_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.StringRelatedField(source='requested_by', read_only=True)
    approved_by_name = serializers.StringRelatedField(source='approved_by', read_only=True)
    student_count = serializers.SerializerMethodField()
    students_data = serializers.SerializerMethodField(source='get_students_data', read_only=True) 
    
    class Meta:
        model = TransferRequest
        fields = [
            'id', 'from_batch', 'from_batch_id','from_batch_code', 'to_batch', 'to_batch_id','to_batch_code',
            'status', 'status_display', 'requested_by', 'requested_by_name',
            'requested_at', 'approved_by', 'approved_by_name', 'approved_at',
            'remarks', 'student_count', 'students_data', 'students'
        ]
        read_only_fields = ['requested_by','requested_at', 'approved_at', 'status', 'approved_by']
        extra_kwargs = {'students': {'write_only': True}}
    
    def get_student_count(self, obj):
        return obj.students.count()
    
    def get_students_data(self, obj):
        return [{"id": s.student_id, "name": f"{s.first_name} {s.last_name or ''}"} for s in obj.students.all()]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['requested_by'] = user
        
        students_data = validated_data.pop('students', [])
        transfer_request = TransferRequest.objects.create(**validated_data)
        if students_data:
            transfer_request.students.set(students_data)
        
        return transfer_request


class TransferRequestDetailSerializer(TransferRequestSerializer):
    students_data = serializers.SerializerMethodField()
    
    class Meta(TransferRequestSerializer.Meta):
        fields = TransferRequestSerializer.Meta.fields + ['students_data']
    
    def get_students_data(self, obj):
        students = obj.students.all()
        return [{
            'id': student.id,
            'name': str(student),
            'email': student.email,
            'phone': student.phone
        } for student in students]


class TransferRequestApprovalSerializer(serializers.Serializer):
    approved_students = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        many=True,
        required=False
    )
    remarks = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        transfer_request = self.context['transfer_request']

        if transfer_request.status != 'PENDING':
            raise serializers.ValidationError("Only pending transfer requests can be approved.")

        if 'approved_students' in data:
            request_students = set(transfer_request.students.values_list('id', flat=True))
            approved_students = set(student.id for student in data['approved_students'])

            if not approved_students.issubset(request_students):
                raise serializers.ValidationError(
                    "Some approved students are not part of this transfer request."
                )

        return data

    def save(self, **kwargs):
        request = self.context['request']
        transfer_request = self.context['transfer_request']

        # If not provided, approve all students in the request
        approved_students = self.validated_data.get(
            'approved_students',
            transfer_request.students.all()
        )

        for student in approved_students:
            # ✅ Create new batch entry for each approved student
            BatchStudent.objects.create(
                batch=transfer_request.to_batch,
                student=student,
                user=request.user
            )

        # ✅ Update transfer request status
        transfer_request.status = "APPROVED"
        transfer_request.remarks = self.validated_data.get("remarks", "")
        transfer_request.save()

        return transfer_request

class TransferRequestRejectionSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        transfer_request = self.context['transfer_request']
        
        if transfer_request.status != 'PENDING':
            raise serializers.ValidationError("Only pending transfer requests can be rejected.")
        
        return data


class TrainerHandoverSerializer(serializers.ModelSerializer):
    batch_id = serializers.StringRelatedField(source='batch', read_only=True)
    from_trainer_name = serializers.StringRelatedField(source='from_trainer', read_only=True)
    to_trainer_name = serializers.StringRelatedField(source='to_trainer', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.StringRelatedField(source='requested_by', read_only=True)
    approved_by_name = serializers.StringRelatedField(source='approved_by', read_only=True)
    
    class Meta:
        model = TrainerHandover
        fields = [
            'id', 'batch', 'batch_id', 'from_trainer', 'from_trainer_name',
            'to_trainer', 'to_trainer_name', 'status', 'status_display',
            'requested_by', 'requested_by_name', 'requested_at',
            'approved_by', 'approved_by_name', 'approved_at', 'remarks'
        ]
        read_only_fields = ['from_trainer', 'requested_by','requested_at', 'approved_at', 'status', 'approved_by']

    def create(self, validated_data):
        user = self.context['request'].user
        batch = validated_data.get('batch')
        
        # Set the from_trainer to the batch's current trainer
        from_trainer = batch.trainer
        
        # Get remarks and handover_date from the request data
        remarks = self.context['request'].data.get('remarks')
        handover_date = self.context['request'].data.get('handover_date')
        
        # Remove remarks, requested_by and handover_date from validated_data to avoid duplicate argument
        validated_data.pop('remarks', None)
        validated_data.pop('requested_by', None)
        validated_data.pop('handover_date', None)
        
        # Create the handover instance
        handover = TrainerHandover.objects.create(
            from_trainer=from_trainer,
            requested_by=user,
            remarks=remarks,
            handover_date=handover_date,
            **validated_data
        )
        return handover


class TrainerHandoverApprovalSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        handover = self.context['handover']
        
        if handover.status != 'PENDING':
            raise serializers.ValidationError("Only pending handover requests can be approved.")
        
        return data


class TrainerHandoverRejectionSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        handover = self.context['handover']
        
        if handover.status != 'PENDING':
            raise serializers.ValidationError("Only pending handover requests can be rejected.")
        
        return data


class BatchTransactionSerializer(serializers.ModelSerializer):
    batch_id = serializers.StringRelatedField(source='batch', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    user_name = serializers.SerializerMethodField()
    affected_students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchTransaction
        fields = [
            'id', 'batch', 'batch_id', 'transaction_type', 'transaction_type_display',
            'user', 'user_name', 'timestamp', 'details', 'affected_students_count'
        ]
        read_only_fields = fields
        
    def get_user_name(self, obj):
        return obj.user.name if obj.user else "System"
    
    def get_affected_students_count(self, obj):
        return obj.affected_students.count()


class BatchTransactionDetailSerializer(BatchTransactionSerializer):
    affected_students_data = serializers.SerializerMethodField()
    
    class Meta(BatchTransactionSerializer.Meta):
        fields = BatchTransactionSerializer.Meta.fields + ['affected_students_data', 'details']
    
    def get_affected_students_data(self, obj):
        students = obj.affected_students.all()
        return [{
            'id': student.id,
            'name': str(student),
            'email': student.email,
            'phone': student.phone
        } for student in students]


class StudentBatchHistorySerializer(serializers.Serializer):
    student_id = serializers.IntegerField()

    def to_representation(self, instance):
        student_id = instance.get('student_id')
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise serializers.ValidationError("Student not found.")

        batch_history_data = BatchStudent.get_student_batch_history(student)

        # Get transaction history
        transactions = BatchTransaction.objects.filter(affected_students=student).order_by('-timestamp')
        transaction_history = [{
            'id': t.id,
            'batch_id': t.batch.batch_id,
            'transaction_type': t.get_transaction_type_display(),
            'timestamp': t.timestamp,
            'details': t.details,
            'user': str(t.user) if t.user else None
        } for t in transactions]

        return {
            'student_id': student.id,
            'student_name': batch_history_data['student_name'],
            'current_batch': batch_history_data['current_batch'],
            'batch_history': batch_history_data['batch_history'],
            'transaction_history': transaction_history
        }