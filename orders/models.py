from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
        ('refunded',   'Refunded'),
    )

    PAYMENT_STATUS = (
        ('unpaid',  'Unpaid'),
        ('paid',    'Paid'),
        ('failed',  'Failed'),
        ('refunded','Refunded'),
    )

    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number      = models.CharField(max_length=20, unique=True)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status    = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    payment_method    = models.CharField(max_length=50, default='mpesa')

    # delivery info
    delivery_address  = models.TextField()
    delivery_city     = models.CharField(max_length=100)
    delivery_phone    = models.CharField(max_length=20)
    delivery_fee      = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    estimated_arrival = models.DateTimeField(null=True, blank=True)

    # amounts
    subtotal          = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total             = models.DecimalField(max_digits=10, decimal_places=2)

    # coupon
    coupon_code       = models.CharField(max_length=50, blank=True)

    # mpesa
    mpesa_code        = models.CharField(max_length=50, blank=True)

    notes             = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.order_number} - {self.user.username}'


class OrderItem(models.Model):
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product      = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)  # snapshot at time of order
    product_slug = models.CharField(max_length=255)
    quantity     = models.PositiveIntegerField()
    unit_price   = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal     = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'


class OrderStatusHistory(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    status     = models.CharField(max_length=20)
    note       = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.order.order_number} -> {self.status}'
