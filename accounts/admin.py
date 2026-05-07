from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, School
from .models import StudentProfile, TeacherProfile, ParentProfile
from .models import AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'role', 'school', 'is_active', 'is_staff']
    list_filter = ['role', 'school', 'is_active', 'is_staff']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'role', 'school')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'school'),
        }),
    )

    search_fields = ['email', 'first_name', 'last_name']
    filter_horizontal = ()


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'county', 'subscription_status', 'is_active']
    list_filter = ['subscription_status', 'is_active']  # Remove is_on_pilot
    search_fields = ['name', 'code', 'county']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_email', 'timestamp']
    search_fields = ['user__email', 'target_email']


admin.site.register(Role)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(ParentProfile)