from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('email', 'username', 'full_name', 'role', 'is_verified', 'is_active', 'date_joined')
    list_filter   = ('role', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'full_name', 'phone')
    ordering      = ('-date_joined',)

    fieldsets = (
        ('Login Info',   {'fields': ('email', 'username', 'password')}),
        ('Personal',     {'fields': ('full_name', 'phone', 'avatar')}),
        ('Role & Status',{'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('OTP',          {'fields': ('otp_code', 'otp_created')}),
        ('Referral',     {'fields': ('referral_code', 'referred_by')}),
        ('Permissions',  {'fields': ('groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'role', 'password1', 'password2'),
        }),
    )