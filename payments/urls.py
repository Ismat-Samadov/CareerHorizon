from django.urls import path
from . import views

urlpatterns = [
    path('create-payment/', views.create_payment, name='create_payment'),
    path('success/', views.payment_success, name='payment_success'),
    path('error/', views.payment_error, name='payment_error'),
    path('result/', views.handle_epoint_result, name='handle_epoint_result'),
]
