from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from carts.models import Cart, CartItem
from products.models import ProductVariant
from accounts.models import CustomerProfile
from orders.models import Order, OrderItem
from payments.models import Payment
import stripe
import os

stripe.api_key = os.environ['STRIPE_SECRET_KEY']


@login_required
def payment_initiate(request):
    # Convert current user's cart into an Order, then create a Stripe Checkout session
    customer = get_object_or_404(CustomerProfile, user=request.user)

    # require an address
    address = customer.address.first()
    if not address:
        messages.error(request, 'Please add a shipping address before checkout.')
        return redirect('address_list')

    cart = Cart.objects.filter(customer=customer).first()
    if not cart or not cart.cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart_detail')

    # Check if there's already a Pending order for this cart to prevent double-payment
    existing_pending = Order.objects.filter(customer=customer, status='Pending').first()
    if existing_pending:
        # Reuse existing pending order and its Stripe session
        payment = Payment.objects.filter(order=existing_pending).first()
        if payment and payment.stripe_session_id:
            try:
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
                if session.payment_status != 'paid':
                    # Session is still valid and not paid, redirect to it
                    return redirect(session.url, permanent=False)
            except Exception:
                pass
        # If we can't reuse the session, delete the old order and create a new one
        existing_pending.delete()

    # create Order
    total = 0
    for ci in cart.cart_items.all():
        total += ci.subtotal

    order = Order.objects.create(customer=customer, address=address, status='Pending', total_amount=total)

    # create order items
    for ci in cart.cart_items.all():
        OrderItem.objects.create(
            order=order,
            product=ci.variant.product,
            price=ci.variant.product.price,
            quantity=ci.quantity
        )

    # build Stripe line items
    line_items = []
    for item in order.orders_items.all():
        unit_amount = int(item.price * 100)
        qty = int(item.quantity)
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': unit_amount,
                'product_data': {
                    'name': item.product.product_name,
                }
            },
            'quantity': qty
        })

    success_url = request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri(reverse('payment_cancel'))

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={'order_id': order.pk}
    )

    # Save session id on Payment record for tracking
    Payment.objects.create(order=order, transaction_id=session.payment_intent or session.id, amount=order.total_amount, stripe_session_id=session.id, method='Card')

    # clear cart
    cart.cart_items.all().delete()
    cart.delete()

    return redirect(session.url, permanent=False)


# @login_required
# def payment_success(request):
#     session_id = request.GET.get('session_id')
#     if not session_id:
#         messages.error(request, 'No payment session provided.')
#         return redirect('cart_detail')

#     try:
#         session = stripe.checkout.Session.retrieve(session_id)
#     except Exception:
#         messages.error(request, 'Unable to retrieve payment session.')
#         return redirect('cart_detail')

#     metadata = {}
#     if session.metadata:
#         if isinstance(session.metadata, dict):
#             metadata = session.metadata
#         elif hasattr(session.metadata, 'to_dict'):
#             metadata = session.metadata.to_dict()
#         else:
#             try:
#                 metadata = dict(session.metadata)
#             except Exception:
#                 metadata = {}

#     order_id = metadata.get('order_id')
#     if not order_id:
#         messages.error(request, 'Order not found in payment session.')
#         return redirect('cart_detail')

#     # order = get_object_or_404(Order, pk=order_id)
#     # order.status = 'Paid'
#     # order.save()

#     # # update Payment record if exists
#     # try:
#     #     payment = Payment.objects.filter(order=order).last()
#     #     if payment:
#     #         payment.transaction_id = session.payment_intent or session.id
#     #         payment.stripe_session_id = session.id
#     #         payment.save()
#     # except Exception:
#     #     pass

#     messages.success(request, f'Payment successful. Thank you for your order! # {order_id}')
#     return redirect('profile')
@login_required
def payment_success(request):
    messages.success(request, f'Payment successful. Thank you for your order! # ')
    return redirect('profile')

@login_required
def payment_cancel(request):
    messages.warning(request, 'Payment was canceled. You can try again.')
    return redirect('cart_detail')

