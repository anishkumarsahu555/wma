from django.urls import path, include
from . import views

app_name = 'wmaApp'  # Add this line to specify the app_name

urlpatterns = [
    path('', views.login_page, name='login_page'),
    path('logout/', views.user_logout, name='logout'),
    path('post_login/', views.post_login, name='post_login'),
    path('home/', views.homepage, name='homepage'),


    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('manage_staff/', views.manage_staff, name='manage_staff'),
    path('manage_customer/', views.manage_customer, name='manage_customer'),
    path('manage_supplier/', views.manage_supplier, name='manage_supplier'),
    path('manage_jar_counter/', views.manage_jar_counter, name='manage_jar_counter'),
    path('manage_location/', views.manage_location, name='manage_location'),
    path('manage_orders/', views.manage_orders, name='manage_orders'),
    path('manage_profile/', views.manage_profile, name='manage_profile'),
    path('manage_expense_group/', views.manage_expense_group, name='manage_expense_group'),
    path('manage_category/', views.manage_category, name='manage_category'),
    path('manage_unit/', views.manage_unit, name='manage_unit'),
    path('manage_hsn_and_tax/', views.manage_hsn_and_tax, name='manage_hsn_and_tax'),
    path('manage_product/', views.manage_product, name='manage_product'),
    path('add_sale/', views.add_sale, name='add_sale'),
]