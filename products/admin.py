from django.contrib import admin
from .models import Category, Product, ProductImage, ProductTag, RecentlyViewed, Wishlist


class ProductImageInline(admin.TabularInline):
    model  = ProductImage
    extra  = 3


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ('name', 'slug', 'parent', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields       = ('name',)
    list_filter         = ('is_active', 'parent')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display        = ('name', 'vendor', 'category', 'price', 'discount', 'stock', 'is_active', 'is_featured', 'is_flash_sale')
    list_filter         = ('is_active', 'is_featured', 'is_flash_sale', 'condition', 'category')
    search_fields       = ('name', 'description', 'vendor__username')
    prepopulated_fields = {'slug': ('name',)}
    inlines             = [ProductImageInline]


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(RecentlyViewed)
admin.site.register(Wishlist)
