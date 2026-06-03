import logging

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from cart.models import Cart
from .models import Order, OrderItem
from .forms import OrderCreateForm

logger = logging.getLogger(__name__)


@login_required
def order_create(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            insufficient = [
                item for item in cart.items.select_related('product').all()
                if item.quantity > item.product.stock
            ]
            if insufficient:
                for item in insufficient:
                    messages.error(
                        request,
                        f'"{item.product.name}" only has {item.product.stock} '
                        f'in stock (requested {item.quantity}).',
                    )
                return render(
                    request, 'orders/create.html', {'cart': cart, 'form': form},
                )

            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    order.user = request.user
                    order.save()
                    for item in cart.items.select_related('product').all():
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            price=item.product.effective_price,
                            quantity=item.quantity,
                        )
                        item.product.stock -= item.quantity
                        item.product.save()
                    cart.clear()
            except Exception:
                logger.exception('Failed to create order for user %s', request.user.pk)
                messages.error(
                    request,
                    'Something went wrong while placing your order. Please try again.',
                )
                return render(
                    request, 'orders/create.html', {'cart': cart, 'form': form},
                )

            messages.success(request, f'Order #{order.pk} placed successfully!')
            return redirect('orders:order_detail', order_id=order.pk)
    else:
        form = OrderCreateForm(initial={
            'shipping_address': request.user.address,
            'city': request.user.city,
            'phone_number': request.user.phone_number,
        })
    return render(request, 'orders/create.html', {'cart': cart, 'form': form})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/list.html', {'orders': orders})


@login_required
def order_cancel(request, order_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.cancel():
        messages.success(request, f'Order #{order.pk} has been cancelled.')
    else:
        messages.error(
            request,
            f'Order #{order.pk} cannot be cancelled (status: {order.get_status_display()}).',
        )
    return redirect('orders:order_detail', order_id=order.pk)
