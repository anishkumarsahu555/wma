from django.urls import path, include
from . import views

app_name = 'wmaApp'  # Add this line to specify the app_name

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('manage_staff/', views.manage_staff, name='manage_staff'),
    path('manage_customer/', views.manage_customer, name='manage_customer'),
    path('manage_product/', views.manage_product, name='manage_product'),
    path('manage_supplier/', views.manage_supplier, name='manage_supplier'),
    path('manage_jar_counter/', views.manage_jar_counter, name='manage_jar_counter'),
    path('manage_location/', views.manage_location, name='manage_location'),
    path('manage_orders/', views.manage_orders, name='manage_orders'),
    path('manage_profile/', views.manage_profile, name='manage_profile'),
    path('manage_expense_group/', views.manage_expense_group, name='manage_expense_group'),
    path('manage_category/', views.manage_category, name='manage_category'),

]