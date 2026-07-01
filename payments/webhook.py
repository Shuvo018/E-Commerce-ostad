from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
import stripe
import os
from django.shortcuts import render, redirect, get_object_or_404


STRIPE_WEBHOOK_SECRET = os.environ['STRIPE_WEBHOOK_SECRET']


def _get_metadata_from_stripe_object(obj):
    metadata = {}
    if isinstance(obj, dict):
        metadata = obj.get('metadata') or {}
    elif hasattr(obj, 'get'):
        try:
            metadata = obj.get('metadata', {})
        except Exception:
            metadata = {}

    if hasattr(metadata, 'to_dict'):
        try:
            metadata = metadata.to_dict()
        except Exception:
            metadata = {}

    return metadata if isinstance(metadata, dict) else {}


def _to_plain_dict(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, 'to_dict'):
        try:
            return obj.to_dict()
        except Exception:
            return {}
    try:
        return dict(obj)
    except Exception:
        return {}


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print('Stripe webhook signature verification failed:', e)
        return HttpResponse(status=400)
    # Convert stripe.Event / StripeObject to plain dict when possible
    event_dict = _to_plain_dict(event)
    if event_dict:
        event = event_dict

    event_type = event.get('type') if isinstance(event, dict) else getattr(event, 'type', None)
    print(event_type)

    if event_type == 'checkout.session.completed':
        if isinstance(event, dict):
            obj = event.get('data', {}).get('object', {})
        else:
            obj = getattr(getattr(event, 'data', {}), 'object', {})
        metadata = _get_metadata_from_stripe_object(obj)
        order_id = metadata.get('order_id')
        if order_id:
            order = Order.objects.filter(pk=order_id).first()
            if order:
                order.status = 'Paid'
                order.save()
                print('checkout.session.completed payment paid')
            else:
                print('Order not found for checkout.session.completed:', order_id)
        else:
            print('Missing order_id metadata for checkout.session.completed')

    elif event.get('type') == 'payment_intent.succeeded':
        if isinstance(event, dict):
            obj = event.get('data', {}).get('object', {})
        else:
            obj = getattr(getattr(event, 'data', {}), 'object', {})
        metadata = _get_metadata_from_stripe_object(obj)
        order_id = metadata.get('order_id')
        if order_id:
            order = Order.objects.filter(pk=order_id).first()
            if order:
                order.status = 'Paid'
                order.save()
                print('payment paid')
            else:
                print('Order not found for payment_intent.succeeded:', order_id)
        else:
            print('Missing order_id metadata for payment_intent.succeeded')

    return HttpResponse(status=200)


