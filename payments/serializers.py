from rest_framework import serializers
from .models import MpesaTransaction


class MpesaSTKSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        # convert 07XX to 2547XX
        value = value.strip().replace(' ', '')
        if value.startswith('0'):
            value = '254' + value[1:]
        elif value.startswith('+'):
            value = value[1:]
        if not value.startswith('254') or len(value) != 12:
            raise serializers.ValidationError('Enter a valid Kenyan phone number e.g. 0712345678')
        return value


class MpesaTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MpesaTransaction
        fields = [
            'id', 'order', 'phone_number', 'amount', 'status',
            'mpesa_receipt_number', 'result_desc', 'created_at'
        ]
