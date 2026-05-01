from django.urls import path
from .views import RegisterView
from .views import CustomTokenObtainPairView, TokenRefreshView
from .views import MeView
from .views import CreateSchoolView
from .views import CreateUserView
from .views import ListUsersView
from .views import UpdateUserRoleView
from .views import DeleteUserView
from .views import UserDetailView
from .views import ApiRootView
from .views import AuditLogListView
from .views import ListStudentsView, StudentDetailView
from .views import AssessmentListCreateView, StudentResultListCreateView
from .views import StudentReportCardView

urlpatterns = [
    path('', ApiRootView.as_view(), name='api-root'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('create-school/', CreateSchoolView.as_view(), name='create-school'),
    path('create-user/', CreateUserView.as_view(), name='create-user'),
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('users/<int:user_id>/role/', UpdateUserRoleView.as_view(), name='update-user-role'),
    path('users/<int:user_id>/delete/', DeleteUserView.as_view(), name='delete-user'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit-logs'),
    path('students/', ListStudentsView.as_view(), name='list-students'),
    path('students/<int:student_id>/', StudentDetailView.as_view(), name='student-detail'),
    path('assessments/', AssessmentListCreateView.as_view(), name='assessments'),
    path('results/', StudentResultListCreateView.as_view(), name='results'),
    path('students/<int:student_id>/report/', StudentReportCardView.as_view(), name='report-card'),
]