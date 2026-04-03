from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings

import stripe

from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem, Payment
)
from .forms import ProductForm


stripe.api_key = settings.STRIPE_SECRET_KEY


def admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)


def product_list(request):
    products = Product.objects.all().order_by('-created_at')

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    category = request.GET.get('category')
    if category:
        products = products.filter(category__id=category)

    categories = Category.objects.all()
    return render(
        request,
        'store/product_list.html',
        {'products': products, 'categories': categories},
    )


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})


@login_required
@admin_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'store/product_create.html', {'form': form})


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_detail', pk=pk)
    else:
        form = ProductForm(instance=product)
    return render(
        request,
        'store/product_edit.html',
        {'form': form, 'product': product}
    )


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(
        request,
        'store/product_confirm_delete.html',
        {'product': product}
    )


@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        color = request.POST.get('color', '')

        if quantity > product.stock:
            from django.contrib import messages
            messages.error(request, "Not enough stock available")
            return redirect('product_detail', pk=pk)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            color=color
        )

        if not created:
            if item.quantity + quantity > product.stock:
                from django.contrib import messages
                messages.error(request, "Stock limit exceeded")
                return redirect('product_detail', pk=pk)
            item.quantity += quantity
        else:
            item.quantity = quantity

        item.save()

    return redirect('cart_view')


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)
    total = sum(item.product.price * item.quantity for item in items)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk)
    item.delete()
    return redirect('cart_view')


@login_required
def order_success(request):
    return render(request, 'store/order_success.html')


def payment_failed(request):
    return render(request, 'store/payment_failed.html')


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = CartItem.objects.filter(cart=cart)
    total = sum(item.product.price * item.quantity for item in items)

    if request.method == 'POST':
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')

        for item in items:
            if item.quantity > item.product.stock:
                from django.contrib import messages
                messages.error(request, f"{item.product.name} is out of stock")
                return redirect('cart_view')

        order = Order.objects.create(
            user=request.user,
            address=address,
            total_price=total
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            item.product.stock -= item.quantity
            item.product.save()

        payment = Payment.objects.create(order=order, method=payment_method)

        if payment_method == 'COD':
            payment.status = 'Pending'
            payment.save()
            items.delete()
            return redirect('order_success')
        elif payment_method == 'STRIPE':
            return redirect('stripe_payment', order_id=order.id)

    return render(request, 'store/checkout.html', {'items': items, 'total': total})


@login_required
def stripe_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    host = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    site_url = f"{protocol}://{host}"

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': f'Order #{order.id}'},
                'unit_amount': int(order.total_price * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f"{site_url}/payment-success/?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}",
        cancel_url=f"{site_url}/payment-failed/",
    )

    return redirect(session.url)


@login_required
def payment_success(request):
    session_id = request.GET.get('session_id')
    order_id = request.GET.get('order_id')

    if session_id:
        session = stripe.checkout.Session.retrieve(session_id)
        stripe_email = session.customer_details.email

        if order_id:
            payment = get_object_or_404(Payment, order_id=order_id)
            payment.status = 'Completed'
            payment.save()

            cart = Cart.objects.get(user=request.user)
            CartItem.objects.filter(cart=cart).delete()

            send_mail(
                subject=f"Order #{order_id} Payment Successful",
                message=f"Hi,\n\nYour payment for order #{order_id} was successful.\n\nThank you for your purchase!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[stripe_email],
                fail_silently=False,
            )
            print(f"Email successfully sent to Stripe customer: {stripe_email}")

    return render(request, 'store/payment_success.html')


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/my_orders.html', {'orders': orders})


def about_view(request):
    return render(request, 'store/about.html')