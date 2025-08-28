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

    # expense group api urls
    path('add_expense_group_api/', add_expense_group_api, name='add_expense_group_api'),
    path('expense_group_list/', ExpenseGroupListJson.as_view(), name='ExpenseGroupListJson'),
    path('delete_expense_group_api/', delete_expense_group_api, name='delete_expense_group_api'),
    path('get_expense_group_detail/', get_expense_group_detail, name='get_expense_group_detail'),
    path('update_expense_group_api/', update_expense_group_api, name='update_expense_group_api'),

    # customer api urls
    path('add_customer_api/', add_customer_api, name='add_customer_api'),
    path('CustomerListJson/', CustomerListJson.as_view(), name='CustomerListJson'),
    path('delete_customer/', delete_customer, name='delete_customer'),
    path('get_customer_detail/', get_customer_detail, name='get_customer_detail'),
    path('update_customer_api/', update_customer_api, name='update_customer_api'),

    # category api urls
    path('add_category_api/', add_category_api, name='add_category_api'),
    path('CategoryListJson/', CategoryListJson.as_view(), name='CategoryListJson'),
    path('delete_category_api/', delete_category_api, name='delete_category_api'),
    path('get_category_detail/', get_category_detail, name='get_category_detail'),
    path('update_category_api/', update_category_api, name='update_category_api'),

    # unit api urls
    path('add_unit_api/', add_unit_api, name='add_unit_api'),
    path('UnitListJson/', UnitListJson.as_view(), name='UnitListJson'),
    path('delete_unit_api/', delete_unit_api, name='delete_unit_api'),
    path('get_unit_detail/', get_unit_detail, name='get_unit_detail'),
    path('update_unit_api/', update_unit_api, name='update_unit_api'),


    # HSN and tax api urls
    path('add_hsn_and_tax_api/', add_hsn_and_tax_api, name='add_hsn_and_tax_api'),
    path('HSNTAXListJson/', HSNTAXListJson.as_view(), name='HSNTAXListJson'),
    path('delete_hsn_and_tax_api/', delete_hsn_and_tax_api, name='delete_hsn_and_tax_api'),
    path('get_hsn_and_tax_detail/', get_hsn_and_tax_detail, name='get_hsn_and_tax_detail'),
    path('update_hsn_and_tax_api/', update_hsn_and_tax_api, name='update_hsn_and_tax_api'),

    # Product api urls
    path('add_product_api/', add_product_api, name='add_product_api'),
    path('ProductListJson/', ProductListJson.as_view(), name='ProductListJson'),
    path('delete_product_api/', delete_product_api, name='delete_product_api'),
    path('get_product_detail/', get_product_detail, name='get_product_detail'),
    path('update_product_api/', update_product_api, name='update_product_api'),

    # Sales api urls
    path('add_sales_api/', add_sales_api, name='add_sales_api'),
    path('SalesListJson/', SalesListJson.as_view(), name='SalesListJson'),
    path('delete_sales_api/', delete_sales_api, name='delete_sales_api'),
    path('update_sales_api/', update_sales_api, name='update_sales_api'),

    # Expense api urls
    path('add_expense_api/', add_expense_api, name='add_expense_api'),
    path('ExpenseListJson/', ExpenseListJson.as_view(), name='ExpenseListJson'),
    path('delete_expense_api/', delete_expense_api, name='delete_expense_api'),
    path('get_expense_detail/', get_expense_detail, name='get_expense_detail'),
    path('update_expense_api/', update_expense_api, name='update_expense_api'),

]
