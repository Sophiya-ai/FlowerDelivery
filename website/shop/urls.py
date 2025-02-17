from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('order_history/', views.view_orders_and_individual_data, name='individual_data'),
    path('cart/', views.cart_view, name='cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update_cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('process_order/', views.process_order, name='process_order'),
    path('order_success/<int:order_id>/', views.order_success, name='order_success'),
    path('add_to_cart_once_more/<int:order_id>/', views.add_to_cart_once_more, name='add_to_cart_once_more'),
    path('product_reviews/<int:product_id>/', views.watch_review, name='product_reviews'),
    path('add_review/<int:product_id>/', views.add_review, name='add_review'),
]