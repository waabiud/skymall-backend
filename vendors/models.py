from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class VendorProfile(models.Model):
    STATUS_CHOICES = (
        ('pending',   'Pending'),
        ('approved',  'Approved'),
        ('suspended', 'Suspended'),
        ('rejected',  'Rejected'),
    )

    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    business_name    = models.CharField(max_length=255)
    business_email   = models.EmailField()
    business_phone   = models.CharField(max_length=20)
    business_address = models.TextField()
    business_logo    = models.ImageField(upload_to='vendors/logos/', blank=True, null=True)
    business_banner  = models.ImageField(upload_to='vendors/banners/', blank=True, null=True)
    description      = models.TextField(blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verified      = models.BooleanField(default=False)

    # payout info
    mpesa_number     = models.CharField(max_length=20, blank=True)
    bank_name        = models.CharField(max_length=100, blank=True)
    bank_account     = models.CharField(max_length=50, blank=True)

    # stats (cached)
    total_sales      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders     = models.PositiveIntegerField(default=0)
    total_products   = models.PositiveIntegerField(default=0)
    rating           = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    joined_at        = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.business_name} ({self.status})'


class VendorWithdrawal(models.Model):
    STATUS_CHOICES = (
        ('pending',   'Pending'),
        ('approved',  'Approved'),
        ('processed', 'Processed'),
        ('rejected',  'Rejected'),
    )

    METHOD_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('bank',  'Bank Transfer'),
    )

    vendor     = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='withdrawals')
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    method     = models.CharField(max_length=20, choices=METHOD_CHOICES, default='mpesa')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference  = models.CharField(max_length=100, blank=True)
    note       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.vendor.business_name} - KES {self.amount} ({self.status})'
