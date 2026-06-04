from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
import random, string

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['email', 'username', 'full_name', 'phone', 'role', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        # generate referral code
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        user = User(**validated_data, referral_code=referral_code)
        user.set_password(password)
        # generate OTP
        user.otp_code    = str(random.randint(100000, 999999))
        user.otp_created = timezone.now()
        user.save()
        return user


class VerifyOTPSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'email', 'username', 'full_name', 'phone',
            'avatar', 'role', 'is_verified', 'referral_code', 'date_joined'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'referral_code', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match'})
        return attrs


class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()