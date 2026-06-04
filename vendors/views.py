from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import VendorProfile, VendorWithdrawal
from .serializers import (
    VendorProfileSerializer, VendorRegisterSerializer,
    VendorWithdrawalSerializer, VendorAnalyticsSerializer
)
from products.models import Product
from products.serializers import ProductListSerializer, ProductCreateUpdateSerializer
from orders.models import Order, OrderItem, OrderStatusHistory
from orders.serializers import OrderSerializer


class IsVendor(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['vendor', 'admin'] and
            hasattr(request.user, 'vendor_profile') and
            request.user.vendor_profile.status == 'approved'
        )


# ── Vendor Registration ───────────────────────────────────────

class VendorRegisterView(generics.CreateAPIView):
    serializer_class   = VendorRegisterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        vendor = serializer.save(user=self.request.user)
        # update user role
        self.request.user.role = 'vendor'
        self.request.user.save(update_fields=['role'])
        return vendor

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data['message'] = 'Vendor application submitted. Awaiting admin approval.'
        return response


class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(VendorProfile, user=self.request.user)


# ── Vendor Analytics ──────────────────────────────────────────

class VendorAnalyticsView(APIView):
    permission_classes = [IsVendor]

    def get(self, request):
        vendor   = request.user.vendor_profile
        products = Product.objects.filter(vendor=request.user)
        orders   = Order.objects.filter(
            items__product__vendor=request.user
        ).distinct()

        # revenue in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_revenue  = OrderItem.objects.filter(
            product__vendor=request.user,
            order__payment_status='paid',
            order__created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        analytics = {
            'total_sales':        vendor.total_sales,
            'total_orders':       orders.count(),
            'total_products':     products.count(),
            'pending_orders':     orders.filter(status='pending').count(),
            'completed_orders':   orders.filter(status='delivered').count(),
            'cancelled_orders':   orders.filter(status='cancelled').count(),
            'low_stock_products': products.filter(stock__lte=5, stock__gt=0).count(),
            'recent_revenue':     recent_revenue,
        }
        return Response(analytics)


# ── Vendor Products ───────────────────────────────────────────

class VendorProductListView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        queryset = Product.objects.filter(vendor=self.request.user)
        # filter by stock status
        stock = self.request.query_params.get('stock')
        if stock == 'low':
            queryset = queryset.filter(stock__lte=5, stock__gt=0)
        elif stock == 'out':
            queryset = queryset.filter(stock=0)
        return queryset


class VendorProductCreateView(generics.CreateAPIView):
    serializer_class   = ProductCreateUpdateSerializer
    permission_classes = [IsVendor]

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)


class VendorProductEditView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = ProductCreateUpdateSerializer
    permission_classes = [IsVendor]
    lookup_field       = 'slug'

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)


class VendorStockUpdateView(APIView):
    permission_classes = [IsVendor]

    def patch(self, request, slug):
        product = get_object_or_404(Product, slug=slug, vendor=request.user)
        stock   = request.data.get('stock')
        if stock is None or int(stock) < 0:
            return Response({'error': 'Invalid stock value'}, status=status.HTTP_400_BAD_REQUEST)
        product.stock = int(stock)
        product.save(update_fields=['stock'])
        return Response({'message': 'Stock updated', 'stock': product.stock})


# ── Vendor Orders ─────────────────────────────────────────────

class VendorOrderListView(generics.ListAPIView):
    serializer_class   = OrderSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        queryset = Order.objects.filter(
            items__product__vendor=self.request.user
        ).distinct().prefetch_related('items', 'history')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class VendorOrderUpdateView(APIView):
    permission_classes = [IsVendor]

    def patch(self, request, order_number):
        order      = get_object_or_404(Order, order_number=order_number)
        new_status = request.data.get('status')

        allowed = ['processing', 'shipped', 'delivered']
        if new_status not in allowed:
            return Response(
                {'error': f'You can only set status to: {", ".join(allowed)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save(update_fields=['status'])

        OrderStatusHistory.objects.create(
            order      = order,
            status     = new_status,
            note       = f'Status updated by vendor',
            changed_by = request.user,
        )

        return Response({'message': f'Order status updated to {new_status}'})


# ── Vendor Withdrawals ────────────────────────────────────────

class VendorWithdrawalListView(generics.ListCreateAPIView):
    serializer_class   = VendorWithdrawalSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return VendorWithdrawal.objects.filter(vendor=self.request.user.vendor_profile)

    def perform_create(self, serializer):
        vendor = self.request.user.vendor_profile
        amount = serializer.validated_data['amount']

        if amount > vendor.total_sales:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Withdrawal amount exceeds available balance')

        serializer.save(vendor=vendor)
