from django.contrib import admin
from .models import MpesaTransaction


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display  = ('order', 'user', 'phone_number', 'amount', 'status', 'mpesa_receipt_number', 'created_at')
    list_filter   = ('status',)
    search_fields = ('order__order_number', 'phone_number', 'mpesa_receipt_number')
    readonly_fields = ('merchant_request_id', 'checkout_request_id', 'mpesa_receipt_number', 'result_code', 'result_desc')
