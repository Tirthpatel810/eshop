"""
URL configuration for eshop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from eshop_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('products/', views.product_list, name='product_list'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('contact/',views.contact, name='contact'),
    path('logout/', views.logout, name='logout'),

    path('products/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='cart_view'),
    path('cart/update/<int:cart_item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.checkout, name='checkout'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/<int:user_id>/', views.reset_password, name='reset_password'),

    path('checkout/', views.checkout, name='checkout'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('order/success/', views.order_success, name='order_success'),

    path('orders/', views.view_order, name='view_order'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('track-order/<int:order_id>/', views.track_order, name='track_order'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
