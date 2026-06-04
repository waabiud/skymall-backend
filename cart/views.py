from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from products.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        return Response(CartSerializer(cart).data)


class CartAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        quantity   = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id, is_active=True)

        if product.stock < quantity:
            return Response(
                {'error': f'Only {product.stock} items available in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = get_or_create_cart(request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            new_qty = item.quantity + quantity
            if new_qty > product.stock:
                return Response(
                    {'error': f'Cannot add more. Only {product.stock} in stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.quantity = new_qty
        else:
            item.quantity = quantity

        item.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, item_id):
        quantity = int(request.data.get('quantity', 1))
        cart     = get_or_create_cart(request.user)
        item     = get_object_or_404(CartItem, id=item_id, cart=cart)

        if quantity < 1:
            item.delete()
            return Response({'message': 'Item removed from cart'})

        if quantity > item.product.stock:
            return Response(
                {'error': f'Only {item.product.stock} in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = quantity
        item.save()
        return Response(CartSerializer(cart).data)


class CartRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        cart = get_or_create_cart(request.user)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        return Response(CartSerializer(cart).data)


class CartClearView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        cart = get_or_create_cart(request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared'})
