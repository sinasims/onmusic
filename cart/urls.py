from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_to_cart, name='cart_add'),
    path('update/', views.update_cart_item, name='cart_update'),
    path('get/', views.get_cart, name='cart_get'),
    path('checkout/', views.checkout, name='cart_checkout'),
    path('verify/', views.payment_callback, name='cart_verify'),
    path('retry/', views.retry_verification, name='cart_retry'),
    path('invoice/<int:order_id>/', views.invoice_view, name='cart_invoice'),
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('coupon/remove/', views.remove_coupon, name='remove_coupon'),
]
