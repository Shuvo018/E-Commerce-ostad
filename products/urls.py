from django.urls import include, path
from .views import product_list
urlpatterns = [
    path('product_list/', product_list, name='product_list'),
]