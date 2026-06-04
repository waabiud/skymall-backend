from rest_framework import serializers
from .models import VendorProfile, VendorWithdrawal
from products.serializers import ProductListSerializer
from orders.serializers import OrderSerializer


class VendorProfileSerializer(serializers.ModelSerializer):
    username     = serializers.CharField(source='user.username', read_only=True)
    email        = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model  = VendorProfile
        fields = [
            'id', 'username', 'email', 'business_name', 'business_email',
            'business_phone', 'business_address', 'business_logo',
            'business_banner', 'description', 'status', 'is_verified',
            'mpesa_number', 'bank_name', 'bank_account',
            'total_sales', 'total_orders', 'total_products', 'rating', 'joined_at'
        ]
        read_only_fields = ['status', 'is_verified', 'total_sales', 'total_orders', 'total_products', 'rating']


class VendorRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VendorProfile
        fields = [
            'business_name', 'business_email', 'business_phone',
            'business_address', 'description', 'mpesa_number'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        if hasattr(user, 'vendor_profile'):
            raise serializers.ValidationError('You already have a vendor profile')
        validated_data['user'] = user
        return super().create(validated_data)


class VendorWithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VendorWithdrawal
        fields = ['id', 'amount', 'method', 'status', 'reference', 'note', 'created_at']
        read_only_fields = ['status', 'reference']


class VendorAnalyticsSerializer(serializers.Serializer):
    total_sales        = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders       = serializers.IntegerField()
    total_products     = serializers.IntegerField()
    pending_orders     = serializers.IntegerField()
    completed_orders   = serializers.IntegerField()
    cancelled_orders   = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    recent_revenue     = serializers.DecimalField(max_digits=12, decimal_places=2)
