from django.db import models
from shared.models import TimeStampMixin
from orders.models import Order

# Create your models here.
class Payment(TimeStampMixin):

    METHOD_CHOICES = [
        ('Card', 'card'),
        ('Mobile Banking', 'mobile_banking'),
        ('Cash on deliver', 'cash_on_deliver')
    ]

    order = models.ForeignKey(to=Order, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=100, choices=METHOD_CHOICES)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Payment - {self.id}'

