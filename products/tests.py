from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    def test_str(self):
        self.assertEqual(str(self.category), 'Electronics')

    def test_get_absolute_url(self):
        url = self.category.get_absolute_url()
        self.assertEqual(url, reverse('products:product_list_by_category', args=['electronics']))

    def test_ordering(self):
        Category.objects.create(name='Appliances', slug='appliances')
        cats = list(Category.objects.values_list('name', flat=True))
        self.assertEqual(cats, ['Appliances', 'Electronics'])


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            category=self.category,
            name='Kurta',
            slug='kurta',
            price=Decimal('1500.00'),
            stock=10,
            available=True,
        )

    def test_str(self):
        self.assertEqual(str(self.product), 'Kurta')

    def test_get_absolute_url(self):
        url = self.product.get_absolute_url()
        self.assertEqual(url, reverse('products:product_detail', args=['kurta']))

    def test_effective_price_no_discount(self):
        self.assertEqual(self.product.effective_price, Decimal('1500.00'))

    def test_effective_price_with_discount(self):
        self.product.discount_price = Decimal('1200.00')
        self.assertEqual(self.product.effective_price, Decimal('1200.00'))

    def test_effective_price_discount_higher_than_price(self):
        self.product.discount_price = Decimal('2000.00')
        self.assertEqual(self.product.effective_price, Decimal('1500.00'))

    def test_discount_percentage(self):
        self.product.discount_price = Decimal('1200.00')
        self.assertEqual(self.product.discount_percentage, 20)

    def test_discount_percentage_no_discount(self):
        self.assertEqual(self.product.discount_percentage, 0)

    def test_in_stock_true(self):
        self.assertTrue(self.product.in_stock)

    def test_in_stock_false_no_stock(self):
        self.product.stock = 0
        self.assertFalse(self.product.in_stock)

    def test_in_stock_false_unavailable(self):
        self.product.available = False
        self.assertFalse(self.product.in_stock)


class ProductListViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Shoes', slug='shoes')
        Product.objects.create(
            category=self.category, name='Chappal', slug='chappal',
            price=Decimal('500.00'), stock=5, available=True,
        )
        Product.objects.create(
            category=self.category, name='Jogger', slug='jogger',
            price=Decimal('3000.00'), stock=0, available=False,
        )

    def test_product_list_all(self):
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 1)

    def test_product_list_by_category(self):
        response = self.client.get(
            reverse('products:product_list_by_category', args=['shoes'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.category)

    def test_product_list_invalid_category(self):
        response = self.client.get(
            reverse('products:product_list_by_category', args=['nonexistent'])
        )
        self.assertEqual(response.status_code, 404)


class ProductDetailViewTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Food', slug='food')
        self.product = Product.objects.create(
            category=cat, name='Biryani Mix', slug='biryani-mix',
            price=Decimal('250.00'), stock=100, available=True,
        )

    def test_detail_view(self):
        response = self.client.get(reverse('products:product_detail', args=['biryani-mix']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'], self.product)

    def test_detail_view_unavailable(self):
        self.product.available = False
        self.product.save()
        response = self.client.get(reverse('products:product_detail', args=['biryani-mix']))
        self.assertEqual(response.status_code, 404)

    def test_detail_view_nonexistent(self):
        response = self.client.get(reverse('products:product_detail', args=['fake']))
        self.assertEqual(response.status_code, 404)


class SearchViewTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Misc', slug='misc')
        Product.objects.create(
            category=cat, name='Shalwar Kameez', slug='shalwar-kameez',
            price=Decimal('2000.00'), stock=5, available=True,
        )
        Product.objects.create(
            category=cat, name='Dupatta', slug='dupatta',
            price=Decimal('800.00'), stock=3, available=True,
        )

    def test_search_with_query(self):
        response = self.client.get(reverse('products:search'), {'q': 'Shalwar'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 1)

    def test_search_empty_query(self):
        response = self.client.get(reverse('products:search'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)

    def test_search_no_results(self):
        response = self.client.get(reverse('products:search'), {'q': 'xyz123'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)
