from urllib import request

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Role, StudentProfile, TeacherProfile, ParentProfile   
from .models import School
from .models import AuditLog
from .models import Assessment, StudentResult


class UpdateUserRoleSerializer(serializers.Serializer):
    role = serializers.CharField()

    def validate_role(self, value):
        if not Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("Role does not exist")
        return value

class CreateUserByAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()
    

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'role']

    def validate_email(self, value):
        request = self.context.get('request')
        if request and User.objects.filter(email=value, school=request.user.school).exists():
           raise serializers.ValidationError("User with this email already exists in this school")
        return value    

    def create(self, validated_data):
        role_name = validated_data.pop('role')
        role = Role.objects.get(name=role_name)

        print("ROLE:", role.name)

        request = self.context.get('request')

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            role=role,
            school=request.user.school  # inherit admin's school
        )
        if role.name == 'teacher':
            TeacherProfile.objects.create(
                user=user,
                staff_id=f"STF{user.id}"
        )

        elif role.name == "parent":
            ParentProfile.objects.create(user=user)

        elif role.name == 'student':
            StudentProfile.objects.create(
            user=user,
            admission_number=f"ADM{user.id}"
        )    

        return user

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name', 'code', 'county']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.name', read_only=True)
    school = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'school']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.email')

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'target_email', 'ip_address', 'timestamp']

class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    school = serializers.CharField(source='user.school.name', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'email', 'username', 'school',
            'admission_number', 'date_of_birth', 'gender', 'grade', 'stream'
        ]

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'title', 'subject', 'grade', 'term', 'max_marks', 'created_at']

class StudentResultSerializer(serializers.ModelSerializer):
    student_email = serializers.CharField(source='student.user.email', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    subject = serializers.CharField(source='assessment.subject', read_only=True)

    class Meta:
        model = StudentResult
        fields = [
            'id', 'student', 'student_email', 'assessment', 'assessment_title',
            'subject', 'raw_score', 'competency_level', 'teacher_remarks', 'date_recorded'
        ]
        read_only_fields = ['competency_level', 'date_recorded']        