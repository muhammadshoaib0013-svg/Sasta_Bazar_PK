from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('shipping_address', 'city', 'phone_number', 'payment_method', 'notes')
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
