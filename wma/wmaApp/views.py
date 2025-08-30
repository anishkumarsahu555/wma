from datetime import datetime

from django.contrib.auth import logout, authenticate, login
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from utils.get_user_id_detail import get_owner_id
from utils.logger import logger
from .models import *
# Create your views here.

@csrf_exempt
@transaction.atomic
def change_password_api(request):
    if request.method == 'POST':
        try:
            password = request.POST.get('password')
            print(password)
            logger.info(
                f"Password change request received for user {request.user.username}"
            )
            data = StaffUser.objects.select_related().get(userID_id=request.user.pk)
            data.password = password
            data.save()
            user = User.objects.select_related().get(pk=request.user.pk)
            user.set_password(password)
            user.save()
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                logger.info("Password changed successfully")
                return JsonResponse({'message': 'success'}, safe=False)
            logger.error("Password change failed")
            return JsonResponse({'message': 'success'}, safe=False)

        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return JsonResponse({'message': 'error'}, safe=False)


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
    today = datetime.today()

    payments_today = Payment.objects.filter(paymentDate=today, isDeleted=False).aggregate(total=Sum('paymentAmount'))['total'] or 0
    jars_in = JarCounter.objects.filter(date=today).aggregate(total=Sum('inJar'))['total'] or 0
    jars_out = JarCounter.objects.filter(date=today).aggregate(total=Sum('outJar'))['total'] or 0
    total_expense = Expense.objects.filter(isDeleted=False).aggregate(total=Sum('expenseAmount'))['total'] or 0
    total_sales = Sales.objects.filter(isDeleted=False).aggregate(total=Sum('totalAmount'))['total'] or 0
    total_customers = Customer.objects.filter(isDeleted=False).count()
    total_staff = StaffUser.objects.filter(isDeleted=False).count()
    total_suppliers = Supplier.objects.filter(isDeleted=False).count()

    # Example dummy data for charts
    months = ["Jan", "Feb", "Mar", "Apr", "May"]
    sales_data = [20000, 25000, 30000, 28000, 35000]
    expense_data = [8000, 10000, 12000, 9500, 14000]
    payments_by_mode = [30000, 20000, 5000]
    top_customers_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
    top_customers_sales = [12000, 10000, 8000, 6000, 4000]

    context = {
        "payments_today": payments_today,
        "jars_in": jars_in,
        "jars_out": jars_out,
        "total_expense": total_expense,
        "total_sales": total_sales,
        "total_customers": total_customers,
        "total_staff": total_staff,
        "total_suppliers": total_suppliers,
        "months": months,
        "sales_data": sales_data,
        "expense_data": expense_data,
        "payments_by_mode": payments_by_mode,
        "top_customers_names": top_customers_names,
        "top_customers_sales": top_customers_sales,
    }
    return render(request, 'wmaApp/dashboard.html',context)

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

def manage_jars(request):
    logger.info("Manage jars is called")
    return render(request, 'wmaApp/jars/manage_jars.html',)

def manage_payments(request):
    logger.info("Manage payments is called")
    return render(request, 'wmaApp/payments/manage_payments.html',)

def my_profile(request):
    instance = get_object_or_404(StaffUser, userID_id=request.user.pk)
    context = {
        'instance': instance
    }
    return render(request, 'wmaApp/profile/my_profile.html', context)