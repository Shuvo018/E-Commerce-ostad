from django.db import models
from accounts.models import CustomerProfile, Address
from shared.models import TimeStampMixin
from products.models import Product

# Create your models here.

class Order(TimeStampMixin):
    STATUS_CHOICES = [
        ('Pending', 'pending'),
        ('Paid', 'paid'),
        ('Shipped', 'shipped'),
        ('Delivered', 'delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    customer = models.ForeignKey(to=CustomerProfile, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(to=Address, on_delete=models.CASCADE, related_name='addresses')
    status = models.CharField(choices=STATUS_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f'Order-{self.id}-{self.customer.user.first_name}_{self.customer.user.last_name}'

class OrderItem(TimeStampMixin):
    order = models.ForeignKey(to=Order, on_delete=models.CASCADE, related_name='orders_items')
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE, related_name='order_items')
    price = models.DecimalField(max_digits=5, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self) -> str:
        return f'Order Item-{self.order.id}-{self.order.customer.user.first_name}_{self.order.customer.user.last_name}'
