from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from products.models import Category, Product
from cart.models import Cart, CartItem
from .models import Order, OrderItem
from .forms import OrderCreateForm


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='orderer', password='pass123')
        cat = Category.objects.create(name='Grocery', slug='grocery')
        self.p1 = Product.objects.create(
            category=cat, name='Rice', slug='rice',
            price=Decimal('500.00'), stock=50, available=True,
        )
        self.p2 = Product.objects.create(
            category=cat, name='Flour', slug='flour',
            price=Decimal('300.00'), stock=30, available=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            shipping_address='123 Main St',
            city='Rawalpindi',
            phone_number='03001234567',
        )
        OrderItem.objects.create(order=self.order, product=self.p1, price=Decimal('500.00'), quantity=2)
        OrderItem.objects.create(order=self.order, product=self.p2, price=Decimal('300.00'), quantity=3)

    def test_str(self):
        self.assertIn('orderer', str(self.order))

    def test_total_cost(self):
        expected = Decimal('500.00') * 2 + Decimal('300.00') * 3
        self.assertEqual(self.order.total_cost, expected)

    def test_is_cancellable_pending(self):
        self.assertTrue(self.order.is_cancellable)

    def test_is_cancellable_confirmed(self):
        self.order.status = 'confirmed'
        self.assertTrue(self.order.is_cancellable)

    def test_is_not_cancellable_shipped(self):
        self.order.status = 'shipped'
        self.assertFalse(self.order.is_cancellable)

    def test_is_not_cancellable_delivered(self):
        self.order.status = 'delivered'
        self.assertFalse(self.order.is_cancellable)

    def test_cancel_success(self):
        old_stock_p1 = self.p1.stock
        old_stock_p2 = self.p2.stock
        result = self.order.cancel()
        self.assertTrue(result)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
        self.p1.refresh_from_db()
        self.p2.refresh_from_db()
        self.assertEqual(self.p1.stock, old_stock_p1 + 2)
        self.assertEqual(self.p2.stock, old_stock_p2 + 3)

    def test_cancel_already_shipped(self):
        self.order.status = 'shipped'
        self.order.save()
        result = self.order.cancel()
        self.assertFalse(result)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')


class OrderItemModelTest(TestCase):
    def test_str(self):
        user = CustomUser.objects.create_user(username='u', password='p')
        cat = Category.objects.create(name='X', slug='x')
        product = Product.objects.create(
            category=cat, name='Widget', slug='widget',
            price=Decimal('100.00'), stock=5, available=True,
        )
        order = Order.objects.create(
            user=user, shipping_address='addr', city='city', phone_number='123',
        )
        item = OrderItem.objects.create(order=order, product=product, price=Decimal('100.00'), quantity=5)
        self.assertEqual(str(item), '5x Widget')

    def test_cost(self):
        user = CustomUser.objects.create_user(username='u2', password='p')
        cat = Category.objects.create(name='Y', slug='y')
        product = Product.objects.create(
            category=cat, name='Gadget', slug='gadget',
            price=Decimal('200.00'), stock=5, available=True,
        )
        order = Order.objects.create(
            user=user, shipping_address='addr', city='city', phone_number='123',
        )
        item = OrderItem.objects.create(order=order, product=product, price=Decimal('200.00'), quantity=3)
        self.assertEqual(item.cost, Decimal('600.00'))


class OrderCreateFormTest(TestCase):
    def test_valid_form(self):
        data = {
            'shipping_address': '456 Street',
            'city': 'Faisalabad',
            'phone_number': '03009876543',
            'payment_method': 'jazzcash',
            'notes': 'Please deliver before 5pm',
        }
        form = OrderCreateForm(data=data)
        self.assertTrue(form.is_valid())

    def test_missing_required(self):
        form = OrderCreateForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('shipping_address', form.errors)
        self.assertIn('city', form.errors)
        self.assertIn('phone_number', form.errors)


class OrderCreateViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='buyer', password='pass123',
            address='Home', city='Lahore', phone_number='03001111111',
        )
        self.client.login(username='buyer', password='pass123')
        cat = Category.objects.create(name='Snacks', slug='snacks')
        self.product = Product.objects.create(
            category=cat, name='Chips', slug='chips',
            price=Decimal('100.00'), stock=20, available=True,
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

    def test_order_create_get(self):
        response = self.client.get(reverse('orders:order_create'))
        self.assertEqual(response.status_code, 200)

    def test_order_create_post(self):
        data = {
            'shipping_address': '789 Blvd',
            'city': 'Multan',
            'phone_number': '03002222222',
            'payment_method': 'cod',
            'notes': '',
        }
        response = self.client.post(reverse('orders:order_create'), data)
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.items.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 18)

    def test_order_create_empty_cart_redirects(self):
        Cart.objects.get(user=self.user).clear()
        response = self.client.get(reverse('orders:order_create'))
        self.assertEqual(response.status_code, 302)

    def test_order_create_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('orders:order_create'))
        self.assertEqual(response.status_code, 302)


class OrderDetailViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='buyer', password='pass123')
        self.client.login(username='buyer', password='pass123')
        self.order = Order.objects.create(
            user=self.user, shipping_address='addr', city='Lahore', phone_number='123',
        )

    def test_order_detail(self):
        response = self.client.get(reverse('orders:order_detail', args=[self.order.pk]))
        self.assertEqual(response.status_code, 200)

    def test_order_detail_other_user(self):
        other = CustomUser.objects.create_user(username='other', password='pass123')
        self.client.login(username='other', password='pass123')
        response = self.client.get(reverse('orders:order_detail', args=[self.order.pk]))
        self.assertEqual(response.status_code, 404)


class OrderListViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='buyer', password='pass123')
        self.client.login(username='buyer', password='pass123')
        Order.objects.create(user=self.user, shipping_address='a', city='b', phone_number='1')
        Order.objects.create(user=self.user, shipping_address='c', city='d', phone_number='2')

    def test_order_list(self):
        response = self.client.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['orders']), 2)


class OrderCancelViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='buyer', password='pass123')
        self.client.login(username='buyer', password='pass123')
        cat = Category.objects.create(name='Z', slug='z')
        self.product = Product.objects.create(
            category=cat, name='Item', slug='item',
            price=Decimal('100.00'), stock=10, available=True,
        )
        self.order = Order.objects.create(
            user=self.user, shipping_address='a', city='b', phone_number='1',
        )
        OrderItem.objects.create(
            order=self.order, product=self.product,
            price=Decimal('100.00'), quantity=2,
        )

    def test_cancel_order(self):
        response = self.client.get(reverse('orders:order_cancel', args=[self.order.pk]))
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 12)
