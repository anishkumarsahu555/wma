from django.urls import path
from .api_view import *

app_name = 'staff_api'

urlpatterns = [
    # staff user api urls
    path('add_staff/', add_staff_api, name='add_staff_api'),
    path('staff_list/', StaffUserListJson.as_view(), name='StaffUserListJson'),
    path('delete_staff/',delete_staff, name='delete_staff'),
    path('get_staff_detail/',get_staff_detail, name='get_staff_detail'),
    path('update_staff_api/',update_staff_api, name='update_staff_api'),

    path('create_customer/', add_customer_api, name='add_customer_api')
]
