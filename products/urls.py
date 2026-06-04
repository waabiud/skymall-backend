from django.urls import path
from . import views

urlpatterns = [
    # categories
    path('categories/',                  views.CategoryListView.as_view(),        name='categories'),

    # special collections — must come BEFORE the slug pattern
    path('featured/',                    views.FeaturedProductsView.as_view(),    name='featured-products'),
    path('flash-sale/',                  views.FlashSaleView.as_view(),           name='flash-sale'),
    path('trending/',                    views.TrendingProductsView.as_view(),    name='trending'),
    path('recently-viewed/',             views.RecentlyViewedView.as_view(),      name='recently-viewed'),
    path('wishlist/',                    views.WishlistView.as_view(),            name='wishlist'),
    path('wishlist/<int:pk>/remove/',    views.WishlistRemoveView.as_view(),      name='wishlist-remove'),

    # vendor management
    path('manage/create/',               views.VendorProductCreateView.as_view(), name='product-create'),
    path('manage/<slug:slug>/',          views.VendorProductUpdateView.as_view(), name='product-manage'),

    # product list and detail — slug LAST
    path('<slug:slug>/',                 views.ProductDetailView.as_view(),       name='product-detail'),
    path('',                             views.ProductListView.as_view(),         name='product-list'),
]