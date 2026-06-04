from django.contrib import admin
from .models import VendorProfile, VendorWithdrawal


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display  = ('business_name', 'user', 'status', 'is_verified', 'total_sales', 'total_orders', 'joined_at')
    list_filter   = ('status', 'is_verified')
    search_fields = ('business_name', 'user__email', 'business_phone')
    actions       = ['approve_vendors', 'suspend_vendors']

    def approve_vendors(self, request, queryset):
        queryset.update(status='approved', is_verified=True)
        # also update user role
        for vendor in queryset:
            vendor.user.role = 'vendor'
            vendor.user.save(update_fields=['role'])
    approve_vendors.short_description = 'Approve selected vendors'

    def suspend_vendors(self, request, queryset):
        queryset.update(status='suspended')
    suspend_vendors.short_description = 'Suspend selected vendors'


@admin.register(VendorWithdrawal)
class VendorWithdrawalAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'amount', 'method', 'status', 'created_at')
    list_filter  = ('status', 'method')
