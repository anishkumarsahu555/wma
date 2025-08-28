from django.contrib.auth import logout, authenticate, login
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from utils.get_owner_detail import get_owner_id
from utils.logger import logger
from .models import *
# Create your views here.



def login_page(request):
    logger.info("Login page called")
    if request.user.is_authenticated:
        return redirect('wmaApp:dashboard')
    return render(request, 'wmaApp/login.html')


def user_logout(request):
    logout(request)
    logger.info("User logged out")
    return redirect("wmaApp:homepage")

@csrf_exempt
def post_login(request):
    if request.method == 'POST':
        username = request.POST.get('userName')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            user_groups = request.user.groups.values_list('name', flat=True)
            if 'Owner' in user_groups or 'Driver' in user_groups or 'Manager' in user_groups :
                return JsonResponse({'message': 'success', 'data': '/home/'}, safe=False)
        return JsonResponse({'message': 'fail'}, safe=False)
    return JsonResponse({'message': 'fail'}, safe=False)

def homepage(request):
    if request.user.is_authenticated:
        if 'Owner' in request.user.groups.values_list('name',
                                                      flat=True) or 'Manager' in request.user.groups.values_list(
            'name', flat=True):
            return redirect('wmaApp:dashboard')
        elif 'Driver' in request.user.groups.values_list('name', flat=True):
            return redirect('wmaApp:dashboard')
        else:
            return redirect("wmaApp:login_page")
    else:
        return redirect("wmaApp:login_page")


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
    logger.info("Manage customer called")
    location = Location.objects.filter(isDeleted=False,  ownerID_id=get_owner_id(request))

    context = {
        'locations': location
    }
    return render(request, 'wmaApp/customer/manage_customer.html', context)


def manage_supplier(request):
    return render(request, 'wmaApp/manage_supplier.html')


def manage_jar_counter(request):
    return render(request, 'wmaApp/manage_jar_counter.html')


def manage_location(request):
    logger.info("Manage location called")
    return render(request, 'wmaApp/location/manage_locations.html')


def manage_orders(request):
    return render(request, 'wmaApp/manage_orders.html')

def manage_profile(request):
    return render(request, 'wmaApp/profile/manage_profile.html')

def manage_expense_group(request):
    logger.info("Manage expense group called")
    return render(request, 'wmaApp/expense_group/manage_expense_group.html')

def manage_category(request):
    logger.info("Manage category called")
    return render(request, 'wmaApp/inventory/manage_category.html')

def manage_unit(request):
    logger.info("Manage unit called")
    return render(request, 'wmaApp/inventory/manage_units.html')

def manage_hsn_and_tax(request):
    logger.info("Manage HSN and Tax called")
    return render(request, 'wmaApp/inventory/manage_tax_and_hsn.html')

def manage_product(request):
    logger.info("Manage product called")
    categories = Category.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))
    taxs = TaxAndHsn.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))
    units = Unit.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))

    context = {
        'categories': categories,
        'taxs': taxs,
        'units': units
    }

    return render(request, 'wmaApp/inventory/manage_products.html', context)

def add_sale(request):
    logger.info("Add sale called")
    return render(request, 'wmaApp/sales/add_sales.html')

def sales_list(request):
    logger.info("Sales list called")
    staffs = StaffUser.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))
    context = {
        'staffs': staffs
    }
    return render(request, 'wmaApp/sales/sales_list.html', context)

def edit_sale(request, id=None):
    logger.info("Edit sale called")
    object = get_object_or_404(Sales, pk=id, isDeleted=False, ownerID_id=get_owner_id(request))
    products = SaleProduct.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request), salesID_id =object.id )

    context = {
        'object': object,
        'products': products
    }
    return render(request, 'wmaApp/sales/edit_sales.html', context)

def manage_expense(request):
    logger.info("Manage expense called")
    instances = ExpenseGroup.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))
    context = {
        'instances': instances
    }

    return render(request, 'wmaApp/expenditure/manage_expenditure.html', context)