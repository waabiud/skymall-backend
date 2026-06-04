from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=100, blank=True)
    image       = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent      = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories'
    )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    CONDITION_CHOICES = (
        ('new',         'New'),
        ('used',        'Used'),
        ('refurbished', 'Refurbished'),
    )

    vendor         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category       = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name           = models.CharField(max_length=255)
    slug           = models.SlugField(unique=True)
    description    = models.TextField()
    price          = models.DecimalField(max_digits=10, decimal_places=2)
    discount       = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage 0-100
    stock          = models.PositiveIntegerField(default=0)
    condition      = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    is_active      = models.BooleanField(default=True)
    is_featured    = models.BooleanField(default=False)
    is_flash_sale  = models.BooleanField(default=False)
    flash_sale_end = models.DateTimeField(null=True, blank=True)
    views_count    = models.PositiveIntegerField(default=0)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        try:
            discount = float(self.discount)
            price    = float(self.price)
            if 0 < discount <= 100:
                return round(price - (price * discount / 100), 2)
            return price
        except Exception:
            return float(self.price)

    @property
    def is_in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image      = models.ImageField(upload_to='products/')
    alt_text   = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.product.name} - image {self.order}'


class ProductTag(models.Model):
    name     = models.CharField(max_length=50, unique=True)
    products = models.ManyToManyField(Product, related_name='tags', blank=True)

    def __str__(self):
        return self.name


class RecentlyViewed(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed')
    product   = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering        = ['-viewed_at']
        unique_together = ['user', 'product']

    def __str__(self):
        return f'{self.user.username} viewed {self.product.name}'


class Wishlist(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'
