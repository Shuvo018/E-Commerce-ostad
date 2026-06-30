from django.db import models

from shared.models import TimeStampMixin

# Create your models here.

class Category(TimeStampMixin):
    category_name = models.CharField(max_length=100)
    slug = models.CharField(unique=True)
    
    def __str__(self) -> str:
        return self.category_name
    
class Product(TimeStampMixin):
    product_name = models.CharField(max_length=100)
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE, related_name='product')
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    stripe_product_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_price_id = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self) -> str:
        return self.product_name
    
class ProductImage(TimeStampMixin):
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='products/images/')


    def __str__(self) -> str:
        return f'Image for {self.product.product_name}'

class ProductVariant(TimeStampMixin):
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE, related_name='product_variants')
    image = models.ImageField(upload_to='products/images/')
    color = models.CharField(max_length=100)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'Image for {self.product.product_name}'
  
