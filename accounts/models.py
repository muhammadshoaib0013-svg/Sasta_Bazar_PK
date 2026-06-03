from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)

    def get_full_address(self):
        parts = [self.address, self.city, self.postal_code]
        return ', '.join(p for p in parts if p)

    def __str__(self):
        return self.username
