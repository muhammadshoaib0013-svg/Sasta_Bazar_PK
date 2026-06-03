from django.test import TestCase, Client
from django.urls import reverse

from .models import CustomUser
from .forms import CustomUserCreationForm, ProfileUpdateForm


class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            phone_number='03001234567',
            address='123 Main St',
            city='Lahore',
            postal_code='54000',
        )

    def test_str(self):
        self.assertEqual(str(self.user), 'testuser')

    def test_get_full_address_all_fields(self):
        self.assertEqual(self.user.get_full_address(), '123 Main St, Lahore, 54000')

    def test_get_full_address_partial(self):
        self.user.postal_code = ''
        self.assertEqual(self.user.get_full_address(), '123 Main St, Lahore')

    def test_get_full_address_empty(self):
        self.user.address = ''
        self.user.city = ''
        self.user.postal_code = ''
        self.assertEqual(self.user.get_full_address(), '')


class CustomUserCreationFormTest(TestCase):
    def test_valid_form(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'phone_number': '03009876543',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
        }
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_missing_email(self):
        data = {
            'username': 'newuser',
            'email': '',
            'phone_number': '03009876543',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
        }
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_password_mismatch(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'phone_number': '03009876543',
            'password1': 'complexpass123!',
            'password2': 'wrongpass123!',
        }
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())


class ProfileUpdateFormTest(TestCase):
    def test_valid_form(self):
        data = {
            'first_name': 'Ali',
            'last_name': 'Khan',
            'email': 'ali@example.com',
            'phone_number': '03001112222',
            'address': '456 Street',
            'city': 'Karachi',
            'postal_code': '75000',
        }
        form = ProfileUpdateForm(data=data)
        self.assertTrue(form.is_valid())


class RegisterViewTest(TestCase):
    def test_register_get(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_post_valid(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'phone_number': '03001234567',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())

    def test_register_post_invalid(self):
        data = {
            'username': '',
            'email': 'bad',
            'password1': 'a',
            'password2': 'b',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 200)


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser', password='testpass123', email='t@t.com',
        )
        self.client.login(username='testuser', password='testpass123')

    def test_profile_get(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_post_valid(self):
        data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@example.com',
            'phone_number': '03005556666',
            'address': '789 Blvd',
            'city': 'Islamabad',
            'postal_code': '44000',
        }
        response = self.client.post(reverse('accounts:profile'), data)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class LoginLogoutViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser', password='testpass123',
        )

    def test_login_get(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_post_valid(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser', 'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
