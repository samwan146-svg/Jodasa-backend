from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, School
from .models import StudentProfile, TeacherProfile
from .models import AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'role', 'school', 'is_active', 'is_staff']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('role', 'school')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'school'),
        }),
    )

    search_fields = ['email']
    filter_horizontal = ()

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_email', 'timestamp']
    search_fields = ['user__email', 'target_email']

admin.site.register(Role)
admin.site.register(School)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)