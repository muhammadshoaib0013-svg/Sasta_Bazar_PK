from django.test import TestCase

from .models import Category, Product


class CategoryModelTest(TestCase):
    def test_str(self):
        cat = Category.objects.create(name='Electronics', slug='electronics')
        self.assertEqual(str(cat), 'Electronics')
