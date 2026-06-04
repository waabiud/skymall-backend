from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductTag, RecentlyViewed, Wishlist


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'image', 'parent', 'subcategories', 'is_active']

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.filter(is_active=True), many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']


class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductTag
        fields = ['id', 'name']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing products"""
    primary_image    = serializers.SerializerMethodField()
    discounted_price = serializers.ReadOnlyField()
    is_in_stock      = serializers.ReadOnlyField()
    category_name    = serializers.CharField(source='category.name', read_only=True)
    vendor_name      = serializers.CharField(source='vendor.username', read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'price', 'discount', 'discounted_price',
            'is_in_stock', 'stock', 'condition', 'is_featured', 'is_flash_sale',
            'flash_sale_end', 'primary_image', 'category_name', 'vendor_name',
            'views_count', 'created_at'
        ]

    def get_primary_image(self, obj):
        image = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image:
            request = self.context.get('request')
            return request.build_absolute_uri(image.image.url) if request else image.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail page"""
    images           = ProductImageSerializer(many=True, read_only=True)
    tags             = ProductTagSerializer(many=True, read_only=True)
    discounted_price = serializers.ReadOnlyField()
    is_in_stock      = serializers.ReadOnlyField()
    category         = CategorySerializer(read_only=True)
    vendor_name      = serializers.CharField(source='vendor.username', read_only=True)
    vendor_id        = serializers.IntegerField(source='vendor.id', read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'discount',
            'discounted_price', 'stock', 'is_in_stock', 'condition',
            'is_featured', 'is_flash_sale', 'flash_sale_end',
            'images', 'tags', 'category', 'vendor_name', 'vendor_id',
            'views_count', 'created_at', 'updated_at'
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = [
            'name', 'slug', 'description', 'category', 'price',
            'discount', 'stock', 'condition', 'is_active',
            'is_featured', 'is_flash_sale', 'flash_sale_end'
        ]

    def create(self, validated_data):
        validated_data['vendor'] = self.context['request'].user
        return super().create(validated_data)


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    class Meta:
        model  = Wishlist
        fields = ['id', 'product', 'product_id', 'added_at']


class RecentlyViewedSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model  = RecentlyViewed
        fields = ['id', 'product', 'viewed_at']