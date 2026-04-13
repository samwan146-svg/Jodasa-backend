from rest_framework.permissions import BasePermission

class IsSubscriptionActive(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        # allow if user has no school yet (e.g., registering)
        if not user.school:
            return True

        school = user.school

        # update status before checking
        school.update_subscription_status()

        # allow only if not expired
        return school.subscription_status in ['trial', 'active']

class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role is not None and
            request.user.role.name == "admin"
        )


class CanCreateSchool(BasePermission):
    def has_permission(self, request, view):
        # Allow if user has no school yet
        if request.user.is_authenticated and request.user.school is None:
            return True

        # Otherwise must be admin
        return (
            request.user.is_authenticated and
            request.user.role is not None and
            request.user.role.name == "admin"
        )