from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid

from .models import Order, OrderItem, OrderStatusHistory
from .serializers import OrderSerializer, CheckoutSerializer
from cart.models import Cart


def generate_order_number():
    return 'SKY' + str(uuid.uuid4()).upper().replace('-', '')[:10]


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # get cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        data         = serializer.validated_data
        delivery_fee = 200  # flat rate — we'll make this dynamic later
        subtotal     = cart.total
        total        = float(subtotal) + delivery_fee

        # create order
        order = Order.objects.create(
            user             = request.user,
            order_number     = generate_order_number(),
            delivery_address = data['delivery_address'],
            delivery_city    = data['delivery_city'],
            delivery_phone   = data['delivery_phone'],
            payment_method   = data['payment_method'],
            delivery_fee     = delivery_fee,
            subtotal         = subtotal,
            total            = total,
            coupon_code      = data.get('coupon_code', ''),
            notes            = data.get('notes', ''),
        )

        # create order items and reduce stock
        for item in cart.items.select_related('product'):
            OrderItem.objects.create(
                order        = order,
                product      = item.product,
                product_name = item.product.name,
                product_slug = item.product.slug,
                quantity     = item.quantity,
                unit_price   = item.product.discounted_price,
                subtotal     = item.subtotal,
            )
            # reduce stock
            item.product.stock -= item.quantity
            item.product.save(update_fields=['stock'])

        # log status history
        OrderStatusHistory.objects.create(
            order      = order,
            status     = 'pending',
            note       = 'Order placed successfully',
            changed_by = request.user,
        )

        # clear cart
        cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    serializer_class   = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items', 'history')


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class   = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_object(self):
        return get_object_or_404(Order, order_number=self.kwargs['order_number'], user=self.request.user)


class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)

        if order.status not in ['pending', 'confirmed']:
            return Response(
                {'error': f'Cannot cancel an order that is {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()

        # restore stock
        for item in order.items.select_related('product'):
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=['stock'])

        OrderStatusHistory.objects.create(
            order      = order,
            status     = 'cancelled',
            note       = 'Order cancelled by customer',
            changed_by = request.user,
        )

        return Response({'message': 'Order cancelled successfully'})
