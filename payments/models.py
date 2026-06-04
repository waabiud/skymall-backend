from django.db import models
from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()


class MpesaTransaction(models.Model):
    STATUS_CHOICES = (
        ('pending',  'Pending'),
        ('success',  'Success'),
        ('failed',   'Failed'),
        ('cancelled','Cancelled'),
    )

    order                = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='mpesa_transactions')
    user                 = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number         = models.CharField(max_length=20)
    amount               = models.DecimalField(max_digits=10, decimal_places=2)
    merchant_request_id  = models.CharField(max_length=100, blank=True)
    checkout_request_id  = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_code          = models.CharField(max_length=10, blank=True)
    result_desc          = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order.order_number} - {self.phone_number} - {self.status}'
