import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Address, CustomerProfile
from carts.models import Cart, CartItem
from orders.models import Order
from payments.models import Payment
from products.models import Category, Product, ProductVariant


class PaymentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        self.address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        self.order = Order.objects.create(
            customer=self.profile, address=self.address, status='Pending',
            total_amount=Decimal('50.00'),
        )

    def test_str_includes_payment_id(self):
        payment = Payment.objects.create(
            order=self.order, transaction_id='txn_123', amount=Decimal('50.00'), method='Card',
        )
        self.assertEqual(str(payment), f'Payment - {payment.id}')


class PaymentInitiateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        category = Category.objects.create(category_name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            product_name='T-Shirt', category=category, slug='t-shirt',
            description='desc', price=Decimal('20.00'),
        )
        self.variant = ProductVariant.objects.create(product=self.product, color='Red', stock=5)
        self.client.force_login(self.user)

    def test_redirects_to_address_list_when_no_address(self):
        cart = Cart.objects.create(customer=self.profile)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        response = self.client.get(reverse('payment'))
        self.assertRedirects(response, reverse('address_list'))

    def test_redirects_to_cart_detail_when_cart_empty(self):
        address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        self.profile.address.add(address)
        response = self.client.get(reverse('payment'))
        self.assertRedirects(response, reverse('cart_detail'))

    @patch('payments.views.stripe.checkout.Session.create')
    def test_successful_initiate_creates_order_and_payment(self, mock_create):
        address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        self.profile.address.add(address)
        cart = Cart.objects.create(customer=self.profile)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)

        mock_session = MagicMock()
        mock_session.id = 'cs_test_123'
        mock_session.payment_intent = 'pi_test_123'
        mock_session.url = 'https://stripe.example.com/checkout/cs_test_123'
        mock_create.return_value = mock_session

        response = self.client.get(reverse('payment'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, mock_session.url)
        order = Order.objects.get(customer=self.profile)
        self.assertEqual(order.total_amount, Decimal('40.00'))
        self.assertTrue(Payment.objects.filter(order=order, stripe_session_id='cs_test_123').exists())
        self.assertFalse(Cart.objects.filter(pk=cart.pk).exists())


class PaymentSuccessViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        self.address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        self.order = Order.objects.create(
            customer=self.profile, address=self.address, status='Pending',
            total_amount=Decimal('40.00'),
        )
        self.client.force_login(self.user)

    def test_no_session_id_redirects_to_cart(self):
        response = self.client.get(reverse('payment_success'))
        self.assertRedirects(response, reverse('cart_detail'))

    @patch('payments.views.stripe.checkout.Session.retrieve')
    def test_marks_order_paid_on_valid_session(self, mock_retrieve):
        mock_session = MagicMock()
        mock_session.metadata = {'order_id': str(self.order.pk)}
        mock_session.payment_intent = 'pi_test_456'
        mock_session.id = 'cs_test_456'
        mock_retrieve.return_value = mock_session

        response = self.client.get(reverse('payment_success'), {'session_id': 'cs_test_456'})

        self.assertRedirects(response, reverse('profile'))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'Paid')

    @patch('payments.views.stripe.checkout.Session.retrieve')
    def test_marks_order_paid_when_metadata_is_stripe_object(self, mock_retrieve):
        mock_metadata = MagicMock()
        mock_metadata.to_dict.return_value = {'order_id': str(self.order.pk)}
        mock_session = MagicMock()
        mock_session.metadata = mock_metadata
        mock_session.payment_intent = 'pi_test_789'
        mock_session.id = 'cs_test_789'
        mock_retrieve.return_value = mock_session

        response = self.client.get(reverse('payment_success'), {'session_id': 'cs_test_789'})

        self.assertRedirects(response, reverse('profile'))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'Paid')


class PaymentCancelViewTests(TestCase):
    def test_cancel_redirects_to_cart_detail(self):
        user = User.objects.create_user(username='jdoe', password='pass1234')
        CustomerProfile.objects.create(user=user, phone='12345')
        self.client.force_login(user)
        response = self.client.get(reverse('payment_cancel'))
        self.assertRedirects(response, reverse('cart_detail'))


class WebhookViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        self.address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        self.order = Order.objects.create(
            customer=self.profile, address=self.address, status='Pending',
            total_amount=Decimal('40.00'),
        )

    @patch('payments.webhook.stripe.Webhook.construct_event')
    def test_webhook_marks_order_paid_when_order_id_metadata_exists(self, mock_construct_event):
        metadata_obj = MagicMock()
        metadata_obj.to_dict.return_value = {'order_id': str(self.order.pk)}
        obj = {'metadata': metadata_obj}
        event = MagicMock()
        event.get.side_effect = lambda key, default=None: {'type': 'payment_intent.succeeded', 'data': {'object': obj}}.get(key, default)
        mock_construct_event.return_value = event

        response = self.client.post(
            reverse('stripe_webhook'),
            data=json.dumps({'id': 'evt_test'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig'
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'Paid')

    @patch('payments.webhook.stripe.Webhook.construct_event')
    def test_webhook_returns_200_when_order_id_missing(self, mock_construct_event):
        obj = {'metadata': {}}
        event = MagicMock()
        event.get.side_effect = lambda key, default=None: {'type': 'payment_intent.succeeded', 'data': {'object': obj}}.get(key, default)
        mock_construct_event.return_value = event

        response = self.client.post(
            reverse('stripe_webhook'),
            data=json.dumps({'id': 'evt_test'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig'
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'Pending')
