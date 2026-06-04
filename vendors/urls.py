from django.urls import path
from . import views

urlpatterns = [
    # registration & profile
    path('register/',                          views.VendorRegisterView.as_view(),      name='vendor-register'),
    path('profile/',                           views.VendorProfileView.as_view(),       name='vendor-profile'),

    # analytics
    path('analytics/',                         views.VendorAnalyticsView.as_view(),     name='vendor-analytics'),

    # products
    path('products/',                          views.VendorProductListView.as_view(),   name='vendor-products'),
    path('products/create/',                   views.VendorProductCreateView.as_view(), name='vendor-product-create'),
    path('products/<slug:slug>/',              views.VendorProductEditView.as_view(),   name='vendor-product-edit'),
    path('products/<slug:slug>/stock/',        views.VendorStockUpdateView.as_view(),   name='vendor-stock-update'),

    # orders
    path('orders/',                            views.VendorOrderListView.as_view(),     name='vendor-orders'),
    path('orders/<str:order_number>/update/',  views.VendorOrderUpdateView.as_view(),   name='vendor-order-update'),

    # withdrawals
    path('withdrawals/',                       views.VendorWithdrawalListView.as_view(),name='vendor-withdrawals'),
]
