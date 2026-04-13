from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import School
from .models import Role

class UpdateUserRoleSerializer(serializers.Serializer):
    role = serializers.CharField()

    def validate_role(self, value):
        from .models import Role
        if not Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("Role does not exist")
        return value

class CreateUserByAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'role']

    def create(self, validated_data):
        role_name = validated_data.pop('role')
        role = Role.objects.get(name=role_name)

        request = self.context.get('request')

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            role=role,
            school=request.user.school  # inherit admin's school
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