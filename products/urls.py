from django.urls import include, path
from .views import product_list, product_detail_view
urlpatterns = [
    path('product_list/', product_list, name='product_list'),
    path('<int:pk>', product_detail_view, name='product_detail'),
]