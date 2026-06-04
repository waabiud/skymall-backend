from django.urls import path
from . import views

urlpatterns = [
    path('mpesa/stk-push/',                        views.MpesaSTKPushView.as_view(),    name='mpesa-stk-push'),
    path('mpesa/status/<str:checkout_request_id>/', views.MpesaSTKStatusView.as_view(), name='mpesa-stk-status'),
    path('mpesa/callback/',                         views.MpesaCallbackView.as_view(),  name='mpesa-callback'),
]
