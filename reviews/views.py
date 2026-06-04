from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count
from products.models import Product
from .models import Review
from .serializers import ReviewSerializer, ProductRatingSummarySerializer


class ProductReviewListView(generics.ListAPIView):
    serializer_class   = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        return Review.objects.filter(product=product).select_related('user')


class ProductRatingSummaryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        reviews = Review.objects.filter(product=product)

        summary = {
            'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            'total_reviews':  reviews.count(),
            'five_star':      reviews.filter(rating=5).count(),
            'four_star':      reviews.filter(rating=4).count(),
            'three_star':     reviews.filter(rating=3).count(),
            'two_star':       reviews.filter(rating=2).count(),
            'one_star':       reviews.filter(rating=1).count(),
        }
        return Response(summary)


class CreateReviewView(generics.CreateAPIView):
    serializer_class   = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        # check if already reviewed
        if Review.objects.filter(user=self.request.user, product=product).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError('You have already reviewed this product')
        serializer.save(user=self.request.user, product=product)


class UpdateDeleteReviewView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


class MarkHelpfulView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.helpful += 1
        review.save(update_fields=['helpful'])
        return Response({'helpful': review.helpful})
