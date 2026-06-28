from django.contrib import admin
from .models import Address, CustomerProfile

# Register your models here.

admin.site.register(CustomerProfile)
admin.site.register(Address)