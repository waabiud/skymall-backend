from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/reviews/',          views.ProductReviewListView.as_view(),    name='product-reviews'),
    path('<slug:slug>/reviews/create/',   views.CreateReviewView.as_view(),         name='create-review'),
    path('<slug:slug>/rating/',           views.ProductRatingSummaryView.as_view(), name='product-rating'),
    path('reviews/<int:pk>/',             views.UpdateDeleteReviewView.as_view(),   name='review-detail'),
    path('reviews/<int:pk>/helpful/',     views.MarkHelpfulView.as_view(),          name='review-helpful'),
]
