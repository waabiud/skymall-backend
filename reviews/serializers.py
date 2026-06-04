from rest_framework import serializers
from .models import Review, ReviewImage


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ReviewImage
        fields = ['id', 'image']


class ReviewSerializer(serializers.ModelSerializer):
    images      = ReviewImageSerializer(many=True, read_only=True)
    username    = serializers.CharField(source='user.username', read_only=True)
    avatar      = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model  = Review
        fields = [
            'id', 'username', 'avatar', 'product', 'rating', 'title',
            'comment', 'is_verified', 'helpful', 'images', 'created_at'
        ]
        read_only_fields = ['is_verified', 'helpful', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # check if user bought the product
        from orders.models import Order
        bought = Order.objects.filter(
            user=validated_data['user'],
            items__product=validated_data['product'],
            payment_status='paid'
        ).exists()
        validated_data['is_verified'] = bought
        return super().create(validated_data)


class ProductRatingSummarySerializer(serializers.Serializer):
    average_rating = serializers.FloatField()
    total_reviews  = serializers.IntegerField()
    five_star      = serializers.IntegerField()
    four_star      = serializers.IntegerField()
    three_star     = serializers.IntegerField()
    two_star       = serializers.IntegerField()
    one_star       = serializers.IntegerField()
