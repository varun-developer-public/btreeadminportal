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
            'days', 'days_per_week', 'hours_per_day', 'batch_percentage',
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
    to_batch_id = serializers.StringRelatedField(source='to_batch', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.StringRelatedField(source='requested_by', read_only=True)
    approved_by_name = serializers.StringRelatedField(source='approved_by', read_only=True)
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TransferRequest
        fields = [
            'id', 'from_batch', 'from_batch_id', 'to_batch', 'to_batch_id',
            'status', 'status_display', 'requested_by', 'requested_by_name',
            'requested_at', 'approved_by', 'approved_by_name', 'approved_at',
            'remarks', 'student_count'
        ]
        read_only_fields = ['requested_at', 'approved_at', 'status', 'approved_by']
    
    def get_student_count(self, obj):
        return obj.students.count()
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['requested_by'] = user
        
        students = self.context['request'].data.get('students', [])
        
        transfer_request = TransferRequest.objects.create(**validated_data)
        
        # Add students to the transfer request
        if students:
            transfer_request.students.set(students)
        
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
        
        # If approved_students is provided, validate that they are part of the transfer request
        if 'approved_students' in data:
            request_students = set(transfer_request.students.values_list('id', flat=True))
            approved_students = set(student.id for student in data['approved_students'])
            
            if not approved_students.issubset(request_students):
                raise serializers.ValidationError("Some approved students are not part of this transfer request.")
        
        return data


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
        read_only_fields = ['requested_at', 'approved_at', 'status', 'approved_by']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['requested_by'] = user
        
        # Ensure from_trainer is the current trainer of the batch
        batch = validated_data['batch']
        validated_data['from_trainer'] = batch.trainer
        
        return TrainerHandover.objects.create(**validated_data)


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
    user_name = serializers.StringRelatedField(source='user', read_only=True)
    affected_students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchTransaction
        fields = [
            'id', 'batch', 'batch_id', 'transaction_type', 'transaction_type_display',
            'user', 'user_name', 'timestamp', 'details', 'affected_students_count'
        ]
        read_only_fields = fields
    
    def get_affected_students_count(self, obj):
        return obj.affected_students.count()


class BatchTransactionDetailSerializer(BatchTransactionSerializer):
    affected_students_data = serializers.SerializerMethodField()
    
    class Meta(BatchTransactionSerializer.Meta):
        fields = BatchTransactionSerializer.Meta.fields + ['affected_students_data']
    
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
    student_name = serializers.CharField(read_only=True)
    batch_history = serializers.SerializerMethodField()
    transaction_history = serializers.SerializerMethodField()
    
    def get_student_name(self, obj):
        try:
            student = Student.objects.get(id=obj['student_id'])
            return str(student)
        except Student.DoesNotExist:
            return "Unknown Student"
    
    def get_batch_history(self, obj):
        try:
            student = Student.objects.get(id=obj['student_id'])
            batch_students = BatchStudent.objects.filter(student=student).order_by('activated_at')
            
            return [{
                'batch_id': bs.batch.batch_id,
                'course': str(bs.batch.course) if bs.batch.course else None,
                'trainer': str(bs.batch.trainer) if bs.batch.trainer else None,
                'activated_at': bs.activated_at,
                'deactivated_at': bs.deactivated_at,
                'is_active': bs.is_active,
                'status': 'Active' if bs.is_active else 'Inactive'
            } for bs in batch_students]
        except Student.DoesNotExist:
            return []
    
    def get_transaction_history(self, obj):
        try:
            student = Student.objects.get(id=obj['student_id'])
            transactions = BatchTransaction.objects.filter(affected_students=student).order_by('-timestamp')
            
            return [{
                'id': t.id,
                'batch_id': t.batch.batch_id,
                'transaction_type': t.get_transaction_type_display(),
                'timestamp': t.timestamp,
                'details': t.details,
                'user': str(t.user) if t.user else None
            } for t in transactions]
        except Student.DoesNotExist:
            return []