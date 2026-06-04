from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from orders.models import Order, OrderStatusHistory
from .models import MpesaTransaction
from .serializers import MpesaSTKSerializer
from .mpesa import stk_push, normalize_phone
import os


class MpesaSTKPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MpesaSTKSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_number = serializer.validated_data['order_number']
        phone_number = serializer.validated_data['phone_number']

        order = get_object_or_404(Order, order_number=order_number, user=request.user)

        if order.payment_status == 'paid':
            return Response({'error': 'Order is already paid'}, status=status.HTTP_400_BAD_REQUEST)

        response = stk_push(phone_number, int(order.total), order_number)

        if response.get('success'):
            inner    = response.get('response', {})
            MpesaTransaction.objects.create(
                order               = order,
                user                = request.user,
                phone_number        = phone_number,
                amount              = order.total,
                checkout_request_id = response.get('checkout_request_id', ''),
                merchant_request_id = inner.get('payment_id', ''),
                status              = 'pending',
            )
            return Response({
                'message':             'STK push sent. Enter your M-Pesa PIN on your phone.',
                'checkout_request_id': response.get('checkout_request_id'),
                'payment_id':          inner.get('payment_id'),
            })

        return Response({
            'error':   'Failed to initiate payment',
            'details': response.get('error', 'Unknown error'),
        }, status=status.HTTP_400_BAD_REQUEST)


class MpesaSTKStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, checkout_request_id):
        try:
            transaction = MpesaTransaction.objects.get(
                checkout_request_id=checkout_request_id,
                user=request.user
            )
            return Response({
                'checkout_request_id': checkout_request_id,
                'status':              transaction.status,
                'mpesa_receipt':       transaction.mpesa_receipt_number,
                'amount':              transaction.amount,
            })
        except MpesaTransaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(APIView):
    """Codian will POST payment result here"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            data   = request.data
            # Codian callback payload
            success            = data.get('success') or data.get('status') == 'completed'
            checkout_request_id= data.get('checkout_request_id', '')
            receipt_number     = data.get('mpesa_transaction_id') or data.get('receipt_number', '')
            result_desc        = data.get('message', '')

            if not checkout_request_id:
                return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

            try:
                transaction = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
            except MpesaTransaction.DoesNotExist:
                return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})

            if success:
                transaction.status               = 'success'
                transaction.mpesa_receipt_number = receipt_number
                transaction.result_desc          = result_desc
                transaction.save()

                order                = transaction.order
                order.payment_status = 'paid'
                order.status         = 'confirmed'
                order.mpesa_code     = receipt_number
                order.save()

                OrderStatusHistory.objects.create(
                    order      = order,
                    status     = 'confirmed',
                    note       = f'Payment confirmed. M-Pesa receipt: {receipt_number}',
                    changed_by = None,
                )
            else:
                transaction.status      = 'failed'
                transaction.result_desc = result_desc
                transaction.save()

        except Exception as e:
            pass  # always return 200 to Codian

        return Response({'success': True, 'message': 'Callback received'})
