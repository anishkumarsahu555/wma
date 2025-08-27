from django.urls import path
from .api_cached_view import *

app_name = 'cached_api'

urlpatterns = [
    # staff user api urls
    path('customer_list_api_cached/', customer_list_api_cached, name='customer_list_api_cached'),
    path('product_list_api_cached/', product_list_api_cached, name='product_list_api_cached'),
    ]