from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()


class Review(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating     = models.IntegerField(choices=RATING_CHOICES)
    title      = models.CharField(max_length=255, blank=True)
    comment    = models.TextField()
    is_verified= models.BooleanField(default=False)  # bought the product
    helpful    = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'product']
        ordering        = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.rating} stars)'


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image  = models.ImageField(upload_to='reviews/')

    def __str__(self):
        return f'Image for review {self.review.id}'
