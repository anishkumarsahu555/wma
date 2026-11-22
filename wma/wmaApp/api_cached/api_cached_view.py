from utils.custom_response import SuccessResponse, ErrorResponse
from django.core.cache import cache

from utils.get_user_id_detail import get_owner_id
from utils.logger import logger
from wmaApp.models import *

def customer_list_api_cached(request):
    ownerid = get_owner_id(request)
    try:
        o_list = []
        cached_customers = cache.get(f'CustomerList{ownerid}')
        if cached_customers:
            o_list = cached_customers
            logger.info("Customer list fetched from cache")

        else:
            obj_list = Customer.objects.select_related("locationID").filter(isDeleted__exact=False, ownerID_id=ownerid).order_by(
                'name')

            for obj in obj_list:
                obj_dic = {
                    'ID': obj.pk,
                    'Name': obj.name,
                    'Location': obj.locationID.name,
                    'Address': obj.address,
                    'Phone': obj.phone,
                    'DisplayDetail': obj.name + ' - ' + obj.locationID.name
                }
                o_list.append(obj_dic)
            cache.set(f'CustomerList{ownerid}', o_list, timeout=None)
        logger.info("Customer list fetched successfully")
        return SuccessResponse("Customer list fetched successfully", data=o_list).to_json_response()
    except Exception as e:
        logger.error(f"Error while fetching customer list: {e}")
        return ErrorResponse("Error while fetching customer list").to_json_response()

def product_list_api_cached(request):
    ownerid = get_owner_id(request)
    try:
        o_list = []
        cached_products = cache.get(f'ProductList{ownerid}')
        if cached_products:
            o_list = cached_products
            logger.info("Product list fetched from cache")

        else:
            obj_list = Product.objects.select_related("unitID", "categoryID", "taxID").filter(isDeleted__exact=False, ownerID_id=ownerid).order_by(
                'productName')

            for obj in obj_list:
                obj_dic = {
                    'ID': obj.pk,
                    'Name': obj.productName,
                    'Rate': obj.rate,
                    'SP': obj.sp,
                    'Unit': obj.unitID.name,
                    'Category': obj.categoryID.name,
                    'Tax': obj.taxID.taxRate,
                    'DisplayDetail': obj.productName + ' - ₹ ' + str(obj.sp) + '/' + obj.unitID.name
                }
                o_list.append(obj_dic)
            cache.set(f'ProductList{ownerid}', o_list, timeout=None)
        logger.info("Product List fetched successfully")
        return SuccessResponse("Product List fetched successfully", data=o_list).to_json_response()
    except Exception as e:
        logger.error(f"Error while fetching Product List: {e}")
        return ErrorResponse("Error while fetching Product List").to_json_response()
