from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Address, CustomerProfile


class AddressModelTests(TestCase):
    def test_str_returns_formatted_address(self):
        address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        self.assertEqual(str(address), 'Bibir Hat, Chittagong, Bangladesh')


class CustomerProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jdoe', password='pass1234', first_name='John', last_name='Doe'
        )

    def test_str_returns_full_name(self):
        profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        self.assertEqual(str(profile), 'John Doe')

    def test_address_can_be_added(self):
        profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        profile.address.add(address)
        self.assertIn(address, profile.address.all())


class RegisterViewTests(TestCase):
    def test_get_register_renders_form(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_post_register_creates_user_and_profile(self):
        response = self.client.post(reverse('register'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='jane@example.com').exists())
        user = User.objects.get(username='jane@example.com')
        self.assertTrue(CustomerProfile.objects.filter(user=user).exists())

    def test_post_register_with_mismatched_passwords_does_not_create_user(self):
        self.client.post(reverse('register'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane2@example.com',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass!',
        })
        self.assertFalse(User.objects.filter(username='jane2@example.com').exists())

    def test_authenticated_user_redirected_away_from_register(self):
        user = User.objects.create_user(username='existing@example.com', password='pass1234')
        self.client.force_login(user)
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('product_list'))


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe@example.com', password='pass1234')

    def test_login_with_valid_credentials_redirects_to_product_list(self):
        response = self.client.post(reverse('login'), {
            'email': 'jdoe@example.com',
            'password': 'pass1234',
        })
        self.assertRedirects(response, reverse('product_list'))

    def test_login_with_invalid_credentials_shows_error(self):
        response = self.client.post(reverse('login'), {
            'email': 'jdoe@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid credentials' in str(m) for m in messages))

    def test_authenticated_user_redirected_away_from_login(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('product_list'))


class LogoutViewTests(TestCase):
    def test_logout_redirects_to_login(self):
        user = User.objects.create_user(username='jdoe@example.com', password='pass1234')
        self.client.force_login(user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe@example.com', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_profile_get_renders_form_for_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_post_updates_phone(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {'phone': '99999'})
        self.assertRedirects(response, reverse('profile'))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, '99999')


class AddressViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jdoe@example.com', password='pass1234')
        self.profile = CustomerProfile.objects.create(user=self.user, phone='12345')
        self.client.force_login(self.user)

    def test_address_create(self):
        response = self.client.post(reverse('address_create'), {
            'country': 'Bangladesh',
            'city': 'Chittagong',
            'postal_code': '4000',
            'street': 'Bibir Hat',
        })
        self.assertRedirects(response, reverse('address_list'))
        self.assertEqual(self.profile.address.count(), 1)

    def test_address_list_shows_only_own_addresses(self):
        address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        self.profile.address.add(address)
        response = self.client.get(reverse('address_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(address, response.context['addresses'])

    def test_address_delete_removes_address(self):
        address = Address.objects.create(
            country='Bangladesh', city='Chittagong', postal_code='4000', street='Bibir Hat'
        )
        self.profile.address.add(address)
        response = self.client.post(reverse('address_delete', args=[address.pk]))
        self.assertRedirects(response, reverse('address_list'))
        self.assertFalse(Address.objects.filter(pk=address.pk).exists())
