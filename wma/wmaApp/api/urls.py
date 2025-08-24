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

    # location api urls
    path('add_location_api/', add_location_api, name='add_location_api'),
    path('LocationListJson/', LocationListJson.as_view(), name='LocationListJson'),
    path('delete_location_api/', delete_location_api, name='delete_location_api'),
    path('get_location_detail/', get_location_detail, name='get_location_detail'),
    path('update_location_api/', update_location_api, name='update_location_api'),

    path('create_customer/', add_customer_api, name='add_customer_api')
]
