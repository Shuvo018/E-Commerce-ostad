from django.shortcuts import render
from .models import Product, Category

# Create your views here.
def product_list(request):
    products = Product.objects.all()
    category_slug = request.GET.get('category', None)

    if category_slug:
        current_category = Category.objects.filter(slug=category_slug).first()

        products = Product.objects.filter(category = current_category)

    return render(request, 'products/product_category.html', {'products': products})



