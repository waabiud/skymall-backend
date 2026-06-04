from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrderItem
        fields = ['id', 'product', 'product_name', 'product_slug', 'quantity', 'unit_price', 'subtotal']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta:
        model  = OrderStatusHistory
        fields = ['id', 'status', 'note', 'changed_by', 'changed_at']


class OrderSerializer(serializers.ModelSerializer):
    items   = OrderItemSerializer(many=True, read_only=True)
    history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status', 'payment_method',
            'delivery_address', 'delivery_city', 'delivery_phone', 'delivery_fee',
            'estimated_arrival', 'subtotal', 'discount_amount', 'total',
            'coupon_code', 'mpesa_code', 'notes', 'items', 'history', 'created_at'
        ]
        read_only_fields = ['order_number', 'status', 'payment_status', 'subtotal', 'total']


class CheckoutSerializer(serializers.Serializer):
    delivery_address = serializers.CharField()
    delivery_city    = serializers.CharField()
    delivery_phone   = serializers.CharField()
    payment_method   = serializers.ChoiceField(choices=['mpesa', 'cash_on_delivery'])
    coupon_code      = serializers.CharField(required=False, allow_blank=True)
    notes            = serializers.CharField(required=False, allow_blank=True)
