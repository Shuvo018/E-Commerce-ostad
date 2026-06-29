from django.shortcuts import render
from .models import Product, Category

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    category_slug = request.GET.get('category', None)
    current_category = None

    if category_slug:
        current_category = Category.objects.filter(slug=category_slug).first()
        if current_category:
            products = products.filter(category=current_category)
        else:
            products = Product.objects.none()

    return render(request, 'products/product_category.html', {
        'products': products,
        'categories': categories,
        'current_category': current_category,
    })

