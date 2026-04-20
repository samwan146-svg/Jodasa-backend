from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsSubscriptionActive(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True

        if not user.school:
            return True        

        school = user.school
        school.update_subscription_status()

        if school.subscription_status == 'expired':
            raise PermissionDenied("Subscription expired. Please renew.")

        return True

class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        
        if request.user.is_authenticated and request.user.is_superuser:
            return True

        return (
            request.user.is_authenticated and
            request.user.role is not None and
            request.user.role.name == "admin"
        )


class CanCreateSchool(BasePermission):
    def has_permission(self, request, view):

        if request.user.is_authenticated and request.user.is_superuser:
            return True

        # Allow if user has no school yet
        if request.user.is_authenticated and request.user.school is None:
            return True

        # Otherwise must be admin
        return (
            request.user.is_authenticated and
            request.user.role is not None and
            request.user.role.name == "admin"
        )