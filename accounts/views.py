from django.shortcuts import render
from rest_framework import generics
from .models import User
from .serializers import RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from .models import School, Role
from .serializers import SchoolSerializer
from .serializers import CreateUserByAdminSerializer
from .permissions import IsAdminUserRole, CanCreateSchool, IsSubscriptionActive
from rest_framework.generics import ListAPIView
from .models import User
from .serializers import UserSerializer
from .permissions import IsAdminUserRole
from rest_framework import status
from django.shortcuts import get_object_or_404
from .serializers import UpdateUserRoleSerializer
from .permissions import IsSubscriptionActive
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import AuditLog
from .serializers import AuditLogSerializer
from django.utils.dateparse import parse_date
from .models import StudentProfile
from .serializers import StudentProfileSerializer


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

class ApiRootView(APIView):
    def get(self, request):
        return Response({
            "message": "Welcome to JODASA API",
            "endpoints": {
                "register": "/api/register/",
                "login": "/api/login/",
                "me": "/api/me/",
                "create_school": "/api/create-school/",
                "create_user": "/api/create-user/",
                "list_users": "/api/users/",
                "user_detail": "/api/users/<id>/",
                "update_role": "/api/users/<id>/role/",
                "delete_user": "/api/users/<id>/delete/",
                "list_students": "/api/students/",
                "student_detail": "/api/students/<id>/"
            }
        })

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id, school=request.user.school)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id, school=request.user.school)

        if user == request.user:
            return Response(
                {"error": "You cannot change your own role"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UpdateUserRoleSerializer(data=request.data)

        if serializer.is_valid():
            role_name = serializer.validated_data['role']
            role = Role.objects.get(name=role_name)

            user.role = role
            user.save()

            AuditLog.objects.create(
                user=request.user,
                action='update_role',
                target_email=user.email,
                ip_address=get_client_ip(request)
            ) 

            return Response({
                "message": "User role updated",
                "email": user.email,
                "new_role": role.name
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListUsersView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'username']

    def get_queryset(self):
        queryset = User.objects.filter(school=self.request.user.school)
        
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role__name=role)

        return queryset
        

class CreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def post(self, request):
        serializer = CreateUserByAdminSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.save()

           

            AuditLog.objects.create(
                user=request.user,
                action='create_user',
                target_email=user.email,
                ip_address=get_client_ip(request)
            )

            return Response({
                "message": "User created successfully",
                "email": user.email,
                "role": user.role.name
            })

        return Response(serializer.errors, status=400)

class CreateSchoolView(APIView):
    permission_classes = [CanCreateSchool]

    def post(self, request):
        serializer = SchoolSerializer(data=request.data)

        if serializer.is_valid():
            school = serializer.save()

            # assign current user to this school
            user = request.user
            user.school = school

            # assign admin role
            admin_role = Role.objects.get(name="admin")
            user.role = admin_role

            user.save()

            return Response({
                "message": "School created successfully",
                "school": serializer.data
            })

        return Response(serializer.errors, status=400)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school = request.user.school

        if school:
            school.update_subscription_status()

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id, school=request.user.school)

        # optional safety: prevent self-delete
        if user == request.user:
            return Response(
                {"error": "You cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = user.email

        AuditLog.objects.create(
                user=request.user,
                action='delete_user',
                target_email=email,
                ip_address=get_client_ip(request)
            )

        user.delete()      

        return Response(
            {"message": "User deleted successfully"},
            status=status.HTTP_200_OK
        )

class ListStudentsView(ListAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    filter_backends = [filters.SearchFilter]
    search_fields = ['user__email', 'admission_number', 'grade', 'stream']

    def get_queryset(self):
        return StudentProfile.objects.filter(
            user__school=self.request.user.school
        )

class StudentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def get(self, request, student_id):
        student = get_object_or_404(
            StudentProfile,
            id=student_id,
            user__school=request.user.school
        )
        serializer = StudentProfileSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, student_id):
        student = get_object_or_404(
            StudentProfile,
            id=student_id,
            user__school=request.user.school
        )
        serializer = StudentProfileSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuditLogListView(ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    filter_backends = [filters.SearchFilter]
    search_fields = ['user__email', 'target_email', 'action']

    def get_queryset(self):
        queryset = AuditLog.objects.filter(
            user__school=self.request.user.school
        ).order_by('-timestamp')

        # 🔥 Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # 🔥 Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(timestamp__date__gte=parse_date(start_date))

        if end_date:
            queryset = queryset.filter(timestamp__date__lte=parse_date(end_date))

        return queryset
# Create your views here.