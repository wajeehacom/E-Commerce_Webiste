from django.contrib import admin
from django.urls import path
from accounts import views as account_views
from store import views as store_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Account routes
    path('account/register/', account_views.register, name='register'),
    path('account/login/', account_views.user_login, name='login'),
    path('account/logout/', account_views.user_logout, name='logout'),
    path('account/edit-profile/', account_views.EditProfileView.as_view(), name='edit_profile'),

    # Store routes
    path('', store_views.product_list, name='product_list'),
    path('product/<int:pk>/', store_views.product_detail, name='product_detail'),
    path('product/create/', store_views.product_create, name='product_create'),
    path('product/update/<int:pk>/', store_views.product_update, name='product_update'),
    path('product/delete/<int:pk>/', store_views.product_delete, name='product_delete'),
    path('cart/', store_views.cart_view, name='cart_view'),
    path('add-to-cart/<int:pk>/', store_views.add_to_cart, name='add_to_cart'),
    path('remove/<int:pk>/', store_views.remove_from_cart, name='remove_from_cart'),
    path('checkout/',store_views.checkout, name='checkout'),
    path('success/', store_views.order_success, name='order_success'),
    path('stripe/<int:order_id>/', store_views.stripe_payment, name='stripe_payment'),
    path('payment-success/', store_views.payment_success, name='payment_success'),
    path('payment-failed/', store_views.payment_failed, name='payment_failed'),
    path('my-orders/', store_views.my_orders, name='my_orders'),

    path('about/', store_views.about_view, name='about'),
    # Forgot password
    path('password-reset/',
     auth_views.PasswordResetView.as_view(template_name='account/password_reset.html'),
     name='password_reset'),

    path('password-reset/done/',
     auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'),
     name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
     auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'),
     name='password_reset_confirm'),

    path('reset/done/',
     auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'),
     name='password_reset_complete')
    
]


# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

