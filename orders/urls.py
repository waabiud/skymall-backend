from django.urls import path
from . import views

urlpatterns = [
    path('checkout/',                          views.CheckoutView.as_view(),    name='checkout'),
    path('',                                   views.OrderListView.as_view(),   name='order-list'),
    path('<str:order_number>/',                views.OrderDetailView.as_view(), name='order-detail'),
    path('<str:order_number>/cancel/',         views.CancelOrderView.as_view(), name='order-cancel'),
]
