---
name: testing-sasta-bazar
description: Test the Sasta Bazar PK Django e-commerce app end-to-end. Use when verifying models, views, forms, or UI changes.
---

# Testing Sasta Bazar PK

## Run Unit Tests

```bash
cd /home/ubuntu/repos/Sasta_Bazar_PK
pytest --cov=products --cov=accounts --cov=orders --cov=cart --cov-report=term-missing -v
```

Expected: 74 tests, 100% coverage across all 4 apps.

## Start Dev Server

```bash
python manage.py migrate --run-syncdb
python manage.py runserver 0.0.0.0:8000
```

## Create Test Data

The app ships with placeholder templates (they render template names only, not full forms). To test routes or views, use the Django test client or shell:

```python
python manage.py shell -c "
from products.models import Category, Product
cat = Category.objects.create(name='Electronics', slug='electronics')
Product.objects.create(category=cat, name='Mobile Phone', slug='mobile-phone', price=25000, stock=10, available=True)
"
```

## Key Routes

| Route | View | Auth Required |
|-------|------|---------------|
| `/` | Product list | No |
| `/search/?q=term` | Product search | No |
| `/category/<slug>/` | Products by category | No |
| `/<slug>/` | Product detail | No |
| `/accounts/register/` | Registration | No |
| `/accounts/login/` | Login | No |
| `/accounts/profile/` | User profile | Yes |
| `/cart/` | Cart detail | Yes |
| `/cart/add/<id>/` | Add to cart | Yes |
| `/orders/` | Order list | Yes |
| `/orders/create/` | Create order | Yes |

## E2E Verification via Django Test Client

Since templates are stubs, browser-based form interaction might not be possible. Use the Django test client to verify POST endpoints:

```python
from django.test import Client
c = Client()

# Register
resp = c.post('/accounts/register/', {
    'username': 'testshop', 'email': 'test@shop.pk',
    'phone_number': '03001234567',
    'password1': 'SecurePass99!', 'password2': 'SecurePass99!',
})
assert resp.status_code == 302  # redirect to /

# Login and add to cart
c.login(username='testshop', password='SecurePass99!')
resp = c.get('/cart/add/1/')
assert resp.status_code == 302  # redirect to /cart/
```

## Notes

- No CI is configured on this repo. Tests must be run locally.
- The project uses SQLite — no external DB setup needed.
- `AUTH_USER_MODEL = 'accounts.CustomUser'` — use `CustomUser` not Django's default User.
- Templates are minimal placeholders. If full UI testing is needed, templates must be built out with actual HTML forms first.

## Devin Secrets Needed

None — this project uses SQLite and has no external service dependencies.
