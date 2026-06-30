from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product, ProductVariant


class CategoryModelTests(TestCase):
    def test_str_returns_category_name(self):
        category = Category.objects.create(category_name='Electronics', slug='electronics')
        self.assertEqual(str(category), 'Electronics')


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(category_name='Books', slug='books')

    def test_str_returns_product_name(self):
        product = Product.objects.create(
            product_name='Django for Beginners',
            category=self.category,
            slug='django-for-beginners',
            description='A great book',
            price=29.99,
        )
        self.assertEqual(str(product), 'Django for Beginners')

    def test_slug_must_be_unique(self):
        Product.objects.create(
            product_name='Book One',
            category=self.category,
            slug='same-slug',
            description='desc',
            price=10,
        )
        with self.assertRaises(Exception):
            Product.objects.create(
                product_name='Book Two',
                category=self.category,
                slug='same-slug',
                description='desc',
                price=15,
            )


class ProductVariantModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(category_name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            product_name='T-Shirt',
            category=self.category,
            slug='t-shirt',
            description='Cotton t-shirt',
            price=15,
        )

    def test_default_stock_is_zero(self):
        variant = ProductVariant.objects.create(product=self.product, color='Red')
        self.assertEqual(variant.stock, 0)

    def test_str_contains_product_name(self):
        variant = ProductVariant.objects.create(product=self.product, color='Blue', stock=5)
        self.assertIn(self.product.product_name, str(variant))


class ProductListViewTests(TestCase):
    def setUp(self):
        self.category_a = Category.objects.create(category_name='Category A', slug='category-a')
        self.category_b = Category.objects.create(category_name='Category B', slug='category-b')
        self.product_a = Product.objects.create(
            product_name='Product A',
            category=self.category_a,
            slug='product-a',
            description='desc',
            price=10,
        )
        self.product_b = Product.objects.create(
            product_name='Product B',
            category=self.category_b,
            slug='product-b',
            description='desc',
            price=20,
        )

    def test_product_list_returns_all_products_without_filter(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 2)

    def test_product_list_filters_by_category_slug(self):
        response = self.client.get(reverse('product_list'), {'category': 'category-a'})
        self.assertEqual(response.status_code, 200)
        products = response.context['products']
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0], self.product_a)
        self.assertEqual(response.context['current_category'], self.category_a)

    def test_product_list_returns_empty_for_unknown_category(self):
        response = self.client.get(reverse('product_list'), {'category': 'does-not-exist'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)


class ProductDetailViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(category_name='Toys', slug='toys')
        self.product = Product.objects.create(
            product_name='Toy Car',
            category=self.category,
            slug='toy-car',
            description='desc',
            price=12,
        )

    def test_product_detail_returns_product_in_context(self):
        response = self.client.get(reverse('product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'], self.product)

    def test_product_detail_shows_message_when_not_found(self):
        response = self.client.get(reverse('product_detail', args=[9999]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['message'], 'Product detail not found')
