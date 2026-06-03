from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from products.models import Category, Product
from .models import Cart, CartItem


class CartModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='buyer', password='pass123')
        self.cart = Cart.objects.create(user=self.user)
        cat = Category.objects.create(name='Tech', slug='tech')
        self.p1 = Product.objects.create(
            category=cat, name='Phone', slug='phone',
            price=Decimal('50000.00'), stock=10, available=True,
        )
        self.p2 = Product.objects.create(
            category=cat, name='Charger', slug='charger',
            price=Decimal('1000.00'), discount_price=Decimal('800.00'),
            stock=20, available=True,
        )

    def test_str(self):
        self.assertEqual(str(self.cart), 'Cart of buyer')

    def test_total_price_empty(self):
        self.assertEqual(self.cart.total_price, 0)

    def test_total_price_with_items(self):
        CartItem.objects.create(cart=self.cart, product=self.p1, quantity=1)
        CartItem.objects.create(cart=self.cart, product=self.p2, quantity=2)
        expected = Decimal('50000.00') + Decimal('800.00') * 2
        self.assertEqual(self.cart.total_price, expected)

    def test_total_items(self):
        CartItem.objects.create(cart=self.cart, product=self.p1, quantity=1)
        CartItem.objects.create(cart=self.cart, product=self.p2, quantity=3)
        self.assertEqual(self.cart.total_items, 4)

    def test_clear(self):
        CartItem.objects.create(cart=self.cart, product=self.p1, quantity=1)
        self.cart.clear()
        self.assertEqual(self.cart.items.count(), 0)


class CartItemModelTest(TestCase):
    def setUp(self):
        user = CustomUser.objects.create_user(username='buyer2', password='pass123')
        self.cart = Cart.objects.create(user=user)
        cat = Category.objects.create(name='Books', slug='books')
        self.product = Product.objects.create(
            category=cat, name='Python Book', slug='python-book',
            price=Decimal('2000.00'), stock=5, available=True,
        )

    def test_str(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)
        self.assertEqual(str(item), '3x Python Book')

    def test_subtotal(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.assertEqual(item.subtotal, Decimal('4000.00'))

    def test_subtotal_with_discount(self):
        self.product.discount_price = Decimal('1500.00')
        self.product.save()
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.assertEqual(item.subtotal, Decimal('3000.00'))


class CartDetailViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='shopper', password='pass123')
        self.client.login(username='shopper', password='pass123')

    def test_cart_detail_creates_cart(self):
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_cart_detail_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.status_code, 302)


class AddToCartViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='shopper', password='pass123')
        self.client.login(username='shopper', password='pass123')
        cat = Category.objects.create(name='Toys', slug='toys')
        self.product = Product.objects.create(
            category=cat, name='Doll', slug='doll',
            price=Decimal('300.00'), stock=10, available=True,
        )

    def test_add_to_cart_new_item(self):
        response = self.client.post(reverse('cart:add_to_cart', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 1)

    def test_add_to_cart_increment(self):
        self.client.post(reverse('cart:add_to_cart', args=[self.product.pk]))
        self.client.post(reverse('cart:add_to_cart', args=[self.product.pk]))
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.first().quantity, 2)

    def test_add_to_cart_get_rejected(self):
        response = self.client.get(reverse('cart:add_to_cart', args=[self.product.pk]))
        self.assertEqual(response.status_code, 405)

    def test_add_to_cart_out_of_stock(self):
        self.product.stock = 0
        self.product.save()
        response = self.client.post(reverse('cart:add_to_cart', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cart.objects.filter(user=self.user, items__product=self.product).exists())


class RemoveFromCartViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='shopper', password='pass123')
        self.client.login(username='shopper', password='pass123')
        cat = Category.objects.create(name='Toys', slug='toys')
        product = Product.objects.create(
            category=cat, name='Ball', slug='ball',
            price=Decimal('200.00'), stock=10, available=True,
        )
        cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=cart, product=product, quantity=1)

    def test_remove_item(self):
        response = self.client.post(reverse('cart:remove_from_cart', args=[self.item.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_remove_item_get_rejected(self):
        response = self.client.get(reverse('cart:remove_from_cart', args=[self.item.pk]))
        self.assertEqual(response.status_code, 405)


class UpdateCartItemViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='shopper', password='pass123')
        self.client.login(username='shopper', password='pass123')
        cat = Category.objects.create(name='Toys', slug='toys')
        product = Product.objects.create(
            category=cat, name='Bat', slug='bat',
            price=Decimal('1500.00'), stock=10, available=True,
        )
        cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=cart, product=product, quantity=1)

    def test_update_quantity(self):
        response = self.client.post(
            reverse('cart:update_cart_item', args=[self.item.pk]),
            {'quantity': '5'},
        )
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 5)

    def test_update_quantity_to_zero_removes(self):
        response = self.client.post(
            reverse('cart:update_cart_item', args=[self.item.pk]),
            {'quantity': '0'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CartItem.objects.filter(pk=self.item.pk).exists())

    def test_update_quantity_invalid_string(self):
        response = self.client.post(
            reverse('cart:update_cart_item', args=[self.item.pk]),
            {'quantity': 'abc'},
        )
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)

    def test_update_cart_item_get_rejected(self):
        response = self.client.get(reverse('cart:update_cart_item', args=[self.item.pk]))
        self.assertEqual(response.status_code, 405)
