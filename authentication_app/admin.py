from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, ManufacturerProfile
from .forms import AdminUserCreateForm

class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreateForm
    model = User
    list_display = ('username', 'email', 'role', 'license_number', 'is_staff')
    list_filter = ('role', 'is_staff')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Role & License'), {'fields': ('role', 'license_number')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'license_number', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'email', 'license_number')
    ordering = ('username',)

admin.site.register(User, UserAdmin)


@admin.register(ManufacturerProfile)
class ManufacturerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'phone', 'contact_email')
    search_fields = ('company_name', 'user__username', 'user__email')
