from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model  = OrderItem
    extra  = 0


class OrderStatusInline(admin.TabularInline):
    model  = OrderStatusHistory
    extra  = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('order_number', 'user', 'status', 'payment_status', 'total', 'created_at')
    list_filter   = ('status', 'payment_status', 'payment_method')
    search_fields = ('order_number', 'user__email', 'mpesa_code')
    inlines       = [OrderItemInline, OrderStatusInline]
