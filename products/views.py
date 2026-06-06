from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from .models import Category, Product, RecentlyViewed, Wishlist
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, WishlistSerializer, RecentlyViewedSerializer
)


# ── Categories ────────────────────────────────────────────────

class CategoryListView(generics.ListAPIView):
    serializer_class   = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # return only top-level categories; subcategories nested inside
        return Category.objects.filter(is_active=True, parent=None)


# ── Products ──────────────────────────────────────────────────

class ProductListView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'vendor')

        # search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()

        # filter by category slug
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # filter by condition
        condition = self.request.query_params.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)

        # filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # filter featured
        featured = self.request.query_params.get('featured')
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)

        # filter flash sales
        flash = self.request.query_params.get('flash_sale')
        if flash == 'true':
            queryset = queryset.filter(is_flash_sale=True, flash_sale_end__gt=timezone.now())

        # filter in stock only
        in_stock = self.request.query_params.get('in_stock')
        if in_stock == 'true':
            queryset = queryset.filter(stock__gt=0)

        # sorting
        sort = self.request.query_params.get('sort', '-created_at')
        allowed_sorts = ['price', '-price', '-created_at', 'created_at', '-views_count']
        if sort in allowed_sorts:
            queryset = queryset.order_by(sort)

        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class   = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field       = 'slug'
    queryset           = Product.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # increment view count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])

        # track recently viewed for logged-in users
        if request.user.is_authenticated:
            RecentlyViewed.objects.update_or_create(
                user=request.user, product=instance
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class FeaturedProductsView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(is_active=True, is_featured=True)[:12]


class FlashSaleView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, is_flash_sale=True, flash_sale_end__gt=timezone.now()
        )


class TrendingProductsView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(is_active=True).order_by('-views_count')[:12]


# ── Vendor product management ─────────────────────────────────

class VendorProductCreateView(generics.CreateAPIView):
    serializer_class   = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role not in ['vendor', 'admin']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only vendors can add products')
        serializer.save(vendor=self.request.user)


class VendorProductUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field       = 'slug'

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)


# ── Wishlist ──────────────────────────────────────────────────

class WishlistView(generics.ListCreateAPIView):
    serializer_class   = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistRemoveView(generics.DestroyAPIView):
    serializer_class   = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


# ── Recently Viewed ───────────────────────────────────────────

class RecentlyViewedView(generics.ListAPIView):
    serializer_class   = RecentlyViewedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RecentlyViewed.objects.filter(user=self.request.user)[:20]

class ProductImageUploadView(APIView):
    """Accept Cloudinary URL and save as ProductImage"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, vendor=request.user)
        image_url = request.data.get('image_url')

        if not image_url:
            return Response({'error': 'image_url is required'},
                          status=status.HTTP_400_BAD_REQUEST)

        # set previous primary images to non-primary
        if request.data.get('is_primary', True):
            product.images.update(is_primary=False)

        img = ProductImage.objects.create(
            product    = product,
            image      = image_url,
            alt_text   = request.data.get('alt_text', product.name),
            is_primary = request.data.get('is_primary', True),
            order      = product.images.count(),
        )

        return Response({
            'id':        img.id,
            'image':     str(img.image),
            'is_primary':img.is_primary,
        }, status=status.HTTP_201_CREATED)


class ProductImageUploadView(APIView):
    """Accept Cloudinary URL and save as ProductImage"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, vendor=request.user)
        image_url = request.data.get('image_url')

        if not image_url:
            return Response({'error': 'image_url is required'},
                          status=status.HTTP_400_BAD_REQUEST)

        # set previous primary images to non-primary
        if request.data.get('is_primary', True):
            product.images.update(is_primary=False)

        img = ProductImage.objects.create(
            product    = product,
            image      = image_url,
            alt_text   = request.data.get('alt_text', product.name),
            is_primary = request.data.get('is_primary', True),
            order      = product.images.count(),
        )

        return Response({
            'id':        img.id,
            'image':     str(img.image),
            'is_primary':img.is_primary,
        }, status=status.HTTP_201_CREATED)


class ProductImageUploadView(APIView):
    """Accept Cloudinary URL and save as ProductImage"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, vendor=request.user)
        image_url = request.data.get('image_url')

        if not image_url:
            return Response({'error': 'image_url is required'},
                          status=status.HTTP_400_BAD_REQUEST)

        # set previous primary images to non-primary
        if request.data.get('is_primary', True):
            product.images.update(is_primary=False)

        img = ProductImage.objects.create(
            product    = product,
            image      = image_url,
            alt_text   = request.data.get('alt_text', product.name),
            is_primary = request.data.get('is_primary', True),
            order      = product.images.count(),
        )

        return Response({
            'id':        img.id,
            'image':     str(img.image),
            'is_primary':img.is_primary,
        }, status=status.HTTP_201_CREATED)
