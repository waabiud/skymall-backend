from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('rider', 'Rider'),
        ('admin', 'Admin'),
    )

    email         = models.EmailField(unique=True)
    username      = models.CharField(max_length=150, unique=True)
    full_name     = models.CharField(max_length=255, blank=True)
    phone         = models.CharField(max_length=20, blank=True)
    avatar        = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role          = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_verified   = models.BooleanField(default=False)
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    date_joined   = models.DateTimeField(auto_now_add=True)
    last_login    = models.DateTimeField(auto_now=True)

    # 2FA / OTP
    otp_code      = models.CharField(max_length=6, blank=True, null=True)
    otp_created   = models.DateTimeField(blank=True, null=True)

    # Referral
    referral_code       = models.CharField(max_length=20, unique=True, blank=True, null=True)
    referred_by         = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals'
    )

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.email} ({self.role})'