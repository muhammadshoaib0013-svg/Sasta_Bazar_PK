from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from cart.models import Cart
from .models import Order, OrderItem
from .forms import OrderCreateForm


@login_required
def order_create(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.effective_price,
                    quantity=item.quantity,
                )
                item.product.stock -= item.quantity
                item.product.save()
            cart.clear()
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
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.cancel()
    return redirect('orders:order_detail', order_id=order.pk)
