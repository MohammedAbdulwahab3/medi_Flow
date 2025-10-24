from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, ManufacturerProfile
from .forms import AdminUserCreateForm

# Customize the admin site header and title
admin.site.site_header = "MediFlow Administration"
admin.site.site_title = "MediFlow Admin Portal"
admin.site.index_title = "Welcome to MediFlow Administration"

# Unregister Django's default User and Group models if they were registered
# This prevents the NoReverseMatch error for 'auth_user_changelist'
try:
    from django.contrib.auth.models import User as DjangoUser
    admin.site.unregister(DjangoUser)
except (admin.sites.NotRegistered, ImportError):
    pass  # Default User model wasn't registered or doesn't exist

try:
    from django.contrib.auth.models import Group
    admin.site.unregister(Group)
except (admin.sites.NotRegistered, ImportError):
    pass

class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreateForm
    model = User
    list_display = ('username', 'email', 'role', 'license_number', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')
    
    # Customize the changelist page title
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Manage Users'
        return super().changelist_view(request, extra_context=extra_context)
    
    # Customize the add page title
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Add User'
        return super().add_view(request, form_url, extra_context=extra_context)
    
    # Customize the change page title
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Edit User'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth', 'gender')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Role & License'), {'fields': ('role', 'license_number', 'national_id', 'emergency_contact')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'license_number', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    search_fields = ('username', 'email', 'license_number', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = ('last_login', 'date_joined')

# Register the custom User model with the custom UserAdmin
admin.site.register(User, UserAdmin)

# Hide Group and other models - only show User in admin
# ManufacturerProfile and PharmacistProfile not registered
