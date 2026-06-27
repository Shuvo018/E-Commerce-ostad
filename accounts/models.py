from django.db import models
from django.contrib.auth.models import User

from shared.models import TimeStampMixin

# Create your models here.

class Address(TimeStampMixin):
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    street = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f'{self.street}, {self.city}, {self.country}'

class CustomerProfile(TimeStampMixin):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=14)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.ManyToManyField(to=Address, blank=True, related_name='customer_profiles')

    def __str__(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'