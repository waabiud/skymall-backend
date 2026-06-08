from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/',        views.RegisterView.as_view(),       name='register'),
    path('verify-otp/',      views.VerifyOTPView.as_view(),      name='verify-otp'),
    path('login/',           views.LoginView.as_view(),          name='login'),
    path('logout/',          views.LogoutView.as_view(),         name='logout'),
    path('request-otp/',     views.RequestOTPView.as_view(),     name='request-otp'),
    path('token/refresh/',   TokenRefreshView.as_view(),         name='token-refresh'),
    path('profile/',         views.ProfileView.as_view(),        name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('google/',          views.GoogleAuthView.as_view(),     name='google-auth'),
]
