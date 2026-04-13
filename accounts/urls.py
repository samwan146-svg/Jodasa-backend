from django.urls import path
from .views import RegisterView
from .views import CustomTokenObtainPairView, TokenRefreshView
from .views import MeView
from .views import CreateSchoolView
from .views import CreateUserView
from .views import ListUsersView
from .views import UpdateUserRoleView
from .views import DeleteUserView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('create-school/', CreateSchoolView.as_view(), name='create-school'),
    path('create-user/', CreateUserView.as_view(), name='create-user'),
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('users/<int:user_id>/role/', UpdateUserRoleView.as_view(), name='update-user-role'),
    path('users/<int:user_id>/delete/', DeleteUserView.as_view(), name='delete-user'),
]