from django.shortcuts import render
from utils.logger import logger
from .models import *
# Create your views here.

def dashboard(request):
    logger.info("Dashboard called")
    return render(request, 'wmaApp/dashboard.html')

def admin_home(request):
    return render(request, 'admin_home.html')

def manage_staff(request):
    logger.info("Manage staff called")
    groups = UserGroup.objects.filter(isDeleted=False)

    context = {
        'groups': groups
    }
    return render(request, 'wmaApp/staff/manage_staff.html',context)


def manage_customer(request):
    return render(request, 'wmaApp/customer/manage_customer.html')


def manage_product(request):
    return render(request, 'wmaApp/manage_product.html')


def manage_supplier(request):
    return render(request, 'wmaApp/manage_supplier.html')


def manage_jar_counter(request):
    return render(request, 'wmaApp/manage_jar_counter.html')


def manage_location(request):
    return render(request, 'wmaApp/location/manage_locations.html')


def manage_orders(request):
    return render(request, 'wmaApp/manage_orders.html')

def manage_profile(request):
    return render(request, 'wmaApp/profile/manage_profile.html')