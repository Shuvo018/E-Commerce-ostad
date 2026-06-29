from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from carts.models import Cart, CartItem
from products.models import ProductVariant
from accounts.models import CustomerProfile
from carts.forms import AddToCartForm, UpdateCartItemForm


# Create your views here.
@login_required
def add_to_cart(request):
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            variant_id = form.cleaned_data['variant_id']
            quantity = form.cleaned_data['quantity']

            variant = get_object_or_404(ProductVariant, pk=int(variant_id))

            if quantity > variant.stock:
                messages.error(request=request, message='Not enough stocks!')
                return redirect('product_detail', pk=variant.product.pk)

            customer = get_object_or_404(CustomerProfile, user=request.user)
            cart, _ = Cart.objects.get_or_create(customer=customer)
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                variant=variant,
                defaults={'quantity': quantity}
            )

            if not created:
                item.quantity += quantity
                item.save()

            messages.success(request=request, message='Added to cart')
            return redirect('cart_detail')

        messages.error(request, 'Invalid Data!')
        return redirect('cart_detail')
    return redirect('product_list')

@login_required
def cart_detail(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    cart, _ = Cart.objects.get_or_create(customer=customer)
    items = cart.cart_items.filter(quantity__gt=0)
    total_price = 0
    for item in items:
        total_price += item.subtotal
    return render(
        request=request,
        template_name='cart/cart_detail.html',
        context={
            'cart': cart,
            'items': items,
            'total_price': total_price
        }
    )


@login_required
def update_cart_item(request, pk):
    item = get_object_or_404(CartItem, pk=pk)
    if request.method == 'POST':
        form = UpdateCartItemForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if quantity > item.variant.stock:
                messages.error(
                    request=request,
                    message='Not enough stock!'
                )
            elif quantity < 1:
                messages.error(
                    request=request,
                    message='Quantity must be at least 1!'
                )
            else:
                item.quantity = quantity
                item.save()
                messages.success(request,'Cart Updated')
        else:
            messages.error(request,'Invaild Data!')
    return redirect('cart_detail')
