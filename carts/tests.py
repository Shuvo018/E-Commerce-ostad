from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomerProfile
from carts.models import Cart, CartItem
from products.models import Category, Product, ProductVariant


class CartModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')

    def test_str_includes_cart_and_customer_ids(self):
        cart = Cart.objects.create(customer=self.profile)
        self.assertEqual(str(cart), f'Cart-{cart.id} of Customer {self.profile.id}')


class CartItemModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        self.cart = Cart.objects.create(customer=self.profile)
        category = Category.objects.create(category_name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            product_name='T-Shirt', category=category, slug='t-shirt',
            description='desc', price=20,
        )
        self.variant = ProductVariant.objects.create(product=self.product, color='Red', stock=10)

    def test_subtotal_is_price_times_quantity(self):
        item = CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=3)
        self.assertEqual(item.subtotal, self.product.price * 3)


class AddToCartViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        category = Category.objects.create(category_name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            product_name='T-Shirt', category=category, slug='t-shirt',
            description='desc', price=20,
        )
        self.variant = ProductVariant.objects.create(product=self.product, color='Red', stock=5)
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse('add_to_cart'), {
            'variant_id': self.variant.id, 'quantity': 1
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_adds_new_item_to_cart(self):
        response = self.client.post(reverse('add_to_cart'), {
            'variant_id': self.variant.id, 'quantity': 2
        })
        self.assertRedirects(response, reverse('cart_detail'))
        item = CartItem.objects.get(variant=self.variant)
        self.assertEqual(item.quantity, 2)

    def test_increments_quantity_for_existing_item(self):
        cart = Cart.objects.create(customer=self.profile)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        self.client.post(reverse('add_to_cart'), {'variant_id': self.variant.id, 'quantity': 2})
        item = CartItem.objects.get(cart=cart, variant=self.variant)
        self.assertEqual(item.quantity, 3)

    def test_rejects_quantity_exceeding_stock(self):
        response = self.client.post(reverse('add_to_cart'), {
            'variant_id': self.variant.id, 'quantity': 100
        })
        self.assertRedirects(response, reverse('product_detail', args=[self.product.pk]))
        self.assertFalse(CartItem.objects.filter(variant=self.variant).exists())

    def test_get_request_redirects_to_product_list(self):
        response = self.client.get(reverse('add_to_cart'))
        self.assertRedirects(response, reverse('product_list'))


class CartDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        category = Category.objects.create(category_name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            product_name='T-Shirt', category=category, slug='t-shirt',
            description='desc', price=20,
        )
        self.variant = ProductVariant.objects.create(product=self.product, color='Red', stock=5)
        self.client.force_login(self.user)

    def test_cart_detail_computes_total_price(self):
        cart = Cart.objects.create(customer=self.profile)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        response = self.client.get(reverse('cart_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_price'], self.product.price * 2)


class UpdateCartItemViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        category = Category.objects.create(category_name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            product_name='T-Shirt', category=category, slug='t-shirt',
            description='desc', price=20,
        )
        self.variant = ProductVariant.objects.create(product=self.product, color='Red', stock=5)
        self.cart = Cart.objects.create(customer=self.profile)
        self.item = CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=1)
        self.client.force_login(self.user)

    def test_update_quantity_within_stock(self):
        response = self.client.post(reverse('update_cart_item', args=[self.item.pk]), {'quantity': 3})
        self.assertRedirects(response, reverse('cart_detail'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 3)

    def test_update_quantity_exceeding_stock_not_applied(self):
        self.client.post(reverse('update_cart_item', args=[self.item.pk]), {'quantity': 999})
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)

    def test_update_quantity_below_one_not_applied(self):
        self.client.post(reverse('update_cart_item', args=[self.item.pk]), {'quantity': 0})
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)
