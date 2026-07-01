from django.urls import path
from .views import payment_initiate, payment_success, payment_cancel
from payments import webhook

# payments/
urlpatterns = [
    path('', payment_initiate, name='payment'),
    path('success/', payment_success, name='payment_success'),
    path('cancel/', payment_cancel, name='payment_cancel'),
    path('webhook/', webhook.stripe_webhook, name='stripe_webhook')
]
