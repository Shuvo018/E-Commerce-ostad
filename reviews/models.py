from django.db import models
from accounts.models import CustomerProfile
from shared.models import TimeStampMixin
from products.models import Product

# Create your models here.

class Review(TimeStampMixin):

    RATING_CHOICES = [
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),
    ]

    customer = models.ForeignKey(to=CustomerProfile, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.CharField(max_length=2, choices=RATING_CHOICES)
    comment = models.CharField(max_length=100, null=True)

    def __str__(self) -> str:
        return f'Review by-{self.customer.user.first_name}_{self.customer.user.last_name} on {self.product.product_name}'
    
    


