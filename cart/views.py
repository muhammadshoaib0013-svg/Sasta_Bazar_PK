from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from products.models import Product
from .models import Cart, CartItem


@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/detail.html', {'cart': cart})


@login_required
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    product = get_object_or_404(Product, id=product_id)
    if not product.in_stock:
        messages.error(request, f'"{product.name}" is out of stock.')
        return redirect('cart:cart_detail')
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect('cart:cart_detail')


@login_required
def remove_from_cart(request, item_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart:cart_detail')


@login_required
def update_cart_item(request, item_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        messages.error(request, 'Invalid quantity.')
        return redirect('cart:cart_detail')
    if quantity > 0:
        item.quantity = quantity
        item.save()
        messages.success(request, 'Cart updated.')
    else:
        item.delete()
        messages.success(request, 'Item removed from cart.')
    return redirect('cart:cart_detail')
