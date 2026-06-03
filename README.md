# Sasta Bazar PK

A Django-based e-commerce platform for affordable shopping in Pakistan.

## Features

- **Products**: Browse categories, search, view product details with discount support
- **Accounts**: User registration, login, profile management
- **Cart**: Add/remove products, update quantities
- **Orders**: Checkout with COD/JazzCash/Easypaisa, order tracking, cancellation

## Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Testing

```bash
pytest --cov=products --cov=accounts --cov=orders --cov=cart --cov-report=term-missing
```
