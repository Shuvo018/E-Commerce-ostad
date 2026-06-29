from django.db import models
from shared.models import TimeStampMixin
from accounts.models import CustomerProfile
from products.models import ProductVariant

# Create your models here.

class Cart(TimeStampMixin):
    Customer = models.ForeignKey(to=CustomerProfile, on_delete=models.CASCADE, related_name='carts')

    def __str__(self) -> str:
        return f'Cart-{self.id} of Customer {self.Customer.id}'

class CartItem(TimeStampMixin):
    cart = models.ForeignKey(to=Cart, on_delete=models.CASCADE, related_name='cart_items')
    variant = models.ForeignKey(to=ProductVariant, on_delete=models.CASCADE, related_name='variants')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.variant.product.price * self.quantity

    def __str__(self) -> str:
        return f'Cart Item-{self.id} of {self.cart.id}'