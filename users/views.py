from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import random
import string

from .serializers import (
    RegisterSerializer, VerifyOTPSerializer, LoginSerializer,
    UserProfileSerializer, ChangePasswordSerializer, RequestOTPSerializer
)

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


def send_otp_email(user):
    try:
        send_mail(
            subject='Your SkyMall Verification Code',
            message=(
                f'Hi {user.full_name or user.username},\n\n'
                f'Your SkyMall verification code is:\n\n'
                f'    {user.otp_code}\n\n'
                f'This code expires in 10 minutes.\n\n'
                f'If you did not request this, please ignore this email.\n\n'
                f'Smart Shopping Starts Here\n'
                f'SkyMall Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            send_otp_email(user)
            return Response({
                'message': f'Registration successful. OTP sent to {user.email}',
                'otp': user.otp_code  # remove in production
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email    = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            if user.otp_created and timezone.now() > user.otp_created + timedelta(minutes=10):
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

            if user.otp_code != otp_code:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            user.is_verified = True
            user.otp_code    = None
            user.otp_created = None
            user.save()

            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Account verified successfully',
                'user': UserProfileSerializer(user).data,
                **tokens
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email    = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user     = authenticate(request, email=email, password=password)

            if not user:
                return Response({'error': 'Invalid email or password'},
                              status=status.HTTP_401_UNAUTHORIZED)
            if not user.is_verified:
                return Response({'error': 'Please verify your account first'},
                              status=status.HTTP_403_FORBIDDEN)

            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                **tokens
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            user.otp_code    = str(random.randint(100000, 999999))
            user.otp_created = timezone.now()
            user.save()
            send_otp_email(user)
            return Response({
                'message': f'OTP sent to {email}',
                'otp': user.otp_code  # remove in production
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'error': 'Old password is incorrect'},
                              status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    """Exchange Google access token for JWT"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        access_token = request.data.get('token')
        email        = request.data.get('email')
        name         = request.data.get('name', '')

        if not access_token or not email:
            return Response({'error': 'Token and email required'},
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            import requests as req
            # verify token with Google
            google_response = req.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )

            if google_response.status_code != 200:
                return Response({'error': 'Invalid Google token'},
                              status=status.HTTP_400_BAD_REQUEST)

            google_data = google_response.json()
            verified_email = google_data.get('email')

            if verified_email != email:
                return Response({'error': 'Email mismatch'},
                              status=status.HTTP_400_BAD_REQUEST)

            # get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0] + str(random.randint(100, 999)),
                    'full_name': name or google_data.get('name', ''),
                    'is_verified': True,
                    'referral_code': ''.join(
                        random.choices(string.ascii_uppercase + string.digits, k=8)
                    ),
                }
            )

            if created:
                user.set_unusable_password()
                user.save()

            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Google login successful',
                'user':    UserProfileSerializer(user).data,
                **tokens
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    """Exchange Google token for JWT"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import requests as req
            # verify token with Google
            google_response = req.get(
                f'https://oauth2.googleapis.com/tokeninfo?id_token={token}'
            )
            google_data = google_response.json()

            if 'error' in google_data:
                return Response({'error': 'Invalid Google token'},
                              status=status.HTTP_400_BAD_REQUEST)

            email    = google_data.get('email')
            name     = google_data.get('name', '')
            picture  = google_data.get('picture', '')

            if not email:
                return Response({'error': 'Email not provided by Google'},
                              status=status.HTTP_400_BAD_REQUEST)

            # get or create user
            import random, string
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username':    email.split('@')[0] + str(random.randint(100, 999)),
                    'full_name':   name,
                    'is_verified': True,
                    'referral_code': ''.join(
                        random.choices(string.ascii_uppercase + string.digits, k=8)
                    ),
                }
            )

            if created:
                user.set_unusable_password()
                user.save()

            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Google login successful',
                'user':    UserProfileSerializer(user).data,
                **tokens
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
