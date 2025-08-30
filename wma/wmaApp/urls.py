from django.urls import path, include
from . import views

app_name = 'wmaApp'  # Add this line to specify the app_name

urlpatterns = [

    path('change_password_api/', views.change_password_api, name='change_password_api'),

    path('', views.login_page, name='login_page'),
    path('logout/', views.user_logout, name='logout'),
    path('post_login/', views.post_login, name='post_login'),
    path('home/', views.homepage, name='homepage'),


    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('manage_staff/', views.manage_staff, name='manage_staff'),
    path('manage_customer/', views.manage_customer, name='manage_customer'),
    path('manage_supplier/', views.manage_supplier, name='manage_supplier'),
    path('manage_location/', views.manage_location, name='manage_location'),
    path('manage_orders/', views.manage_orders, name='manage_orders'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path('manage_expense_group/', views.manage_expense_group, name='manage_expense_group'),
    path('manage_category/', views.manage_category, name='manage_category'),
    path('manage_unit/', views.manage_unit, name='manage_unit'),
    path('manage_hsn_and_tax/', views.manage_hsn_and_tax, name='manage_hsn_and_tax'),
    path('manage_product/', views.manage_product, name='manage_product'),
    path('add_sale/', views.add_sale, name='add_sale'),
    path('manage_sale/', views.sales_list, name='manage_sale'),
    path('edit_sale/<int:id>/', views.edit_sale, name='edit_sale'),
    path('manage_expense/', views.manage_expense, name='manage_expense'),
    path('manage_jars/', views.manage_jars, name='manage_jars'),
    path('manage_payments/', views.manage_payments, name='manage_payments'),
]