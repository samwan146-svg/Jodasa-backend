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

class UpdateUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id, school=request.user.school)

        serializer = UpdateUserRoleSerializer(data=request.data)

        if serializer.is_valid():
            role_name = serializer.validated_data['role']
            role = Role.objects.get(name=role_name)

            user.role = role
            user.save()

            return Response({
                "message": "User role updated",
                "email": user.email,
                "new_role": role.name
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListUsersView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def get_queryset(self):
        # only return users in the same school
        return User.objects.filter(school=self.request.user.school)

class CreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def post(self, request):
        serializer = CreateUserByAdminSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.save()
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

from rest_framework import status
from django.shortcuts import get_object_or_404

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

        user.delete()

        return Response(
            {"message": "User deleted successfully"},
            status=status.HTTP_200_OK
        )    
# Create your views here.