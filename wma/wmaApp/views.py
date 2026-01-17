import datetime
import json

from django.utils import timezone

from django.contrib.auth import logout, authenticate, login
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from utils.check_group_with_authentication import check_groups
from utils.get_user_id_detail import get_owner_id
from utils.logger import logger
from .models import *
# Create your views here.
from django.views.decorators.cache import cache_page

@csrf_exempt
@transaction.atomic
def change_password_api(request):
    if request.method == "POST":
        try:
            password = request.POST.get("password")
            logger.info(
                f"Password change request received for user {request.user.username}"
            )
            try:
                data = StaffUser.objects.select_related().get(userID_id=request.user.pk)
                data.password = password
                data.save()
            except:
                data = Owner.objects.select_related().get(userID_id=request.user.pk)
                data.password = password
                data.save()
            user = User.objects.select_related().get(pk=request.user.pk)
            user.set_password(password)
            user.save()
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                logger.info("Password changed successfully")
                return JsonResponse({"message": "success"}, safe=False)
            logger.error("Password change failed")
            return JsonResponse({"message": "success"}, safe=False)

        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return JsonResponse({"message": "error"}, safe=False)


def login_page(request):
    logger.info("Login page called")
    if request.user.is_authenticated:
        return redirect("wmaApp:dashboard")
    return render(request, "wmaApp/login.html")


def user_logout(request):
    logout(request)
    logger.info("User logged out")
    return redirect("wmaApp:homepage")


@csrf_exempt
def post_login(request):
    if request.method == "POST":
        username = request.POST.get("userName")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            user_groups = request.user.groups.values_list("name", flat=True)
            if (
                "Owner" in user_groups
                or "Driver" in user_groups
                or "Manager" in user_groups
            ):
                return JsonResponse(
                    {"message": "success", "data": "/home/"}, safe=False
                )
        return JsonResponse({"message": "fail"}, safe=False)
    return JsonResponse({"message": "fail"}, safe=False)


def homepage(request):
    if request.user.is_authenticated:
        if "Owner" in request.user.groups.values_list(
            "name", flat=True
        ) or "Manager" in request.user.groups.values_list("name", flat=True):
            return redirect("wmaApp:dashboard")
        elif "Driver" in request.user.groups.values_list("name", flat=True):
            return redirect("wmaApp:dashboard")
        else:
            return redirect("wmaApp:login_page")
    else:
        return redirect("wmaApp:login_page")


@cache_page(60 * 5)  # Cache for 5 minutes
@check_groups("Owner", "Manager", "Admin", "Driver")
def dashboard(request):
    logger.info("Dashboard called")
    owner_id = get_owner_id(request)
    today = datetime.datetime.today()
    if "Driver" not in request.user.groups.values_list("name", flat=True):
        payments_today = (
            Payment.objects.filter(
                paymentDate=today, isDeleted=False, ownerID_id=owner_id
            ).aggregate(total=Sum("paymentAmount"))["total"]
            or 0
        )
        jars_in = (
            JarCounter.objects.filter(
                date=today, ownerID_id=owner_id, isDeleted=False
            ).aggregate(total=Sum("inJar"))["total"]
            or 0
        )
        jars_out = (
            JarCounter.objects.filter(
                date=today, ownerID_id=owner_id, isDeleted=False
            ).aggregate(total=Sum("outJar"))["total"]
            or 0
        )
        total_expense = (
            Expense.objects.filter(
                isDeleted=False, ownerID_id=owner_id, expenseDate=today
            ).aggregate(total=Sum("expenseAmount"))["total"]
            or 0
        )
        total_sales = (
            Sales.objects.filter(
                isDeleted=False, ownerID_id=owner_id, saleDate=today
            ).aggregate(total=Sum("totalAmount"))["total"]
            or 0
        )
        total_customers = Customer.objects.filter(
            isDeleted=False, ownerID_id=owner_id
        ).count()
        total_staff = StaffUser.objects.filter(
            isDeleted=False, ownerID_id=owner_id
        ).count()
        total_suppliers = Supplier.objects.filter(
            isDeleted=False, ownerID_id=owner_id
        ).count()
        total_locations = Location.objects.filter(
            isDeleted=False, ownerID_id=owner_id
        ).count()

        today = timezone.now().date()
        seven_days_ago = today - datetime.timedelta(
            days=6
        )  # last 7 days including today

        # Get sales grouped by date
        sales_data = (
            Sales.objects.filter(
                saleDate__range=[seven_days_ago, today],
                isDeleted=False,
                ownerID_id=owner_id,
            )
            .values("saleDate")  # directly group by date
            .annotate(total=Sum("totalAmountAfterTax"))
            .order_by("saleDate")
        )
        # Get sales grouped by date
        payment_data = (
            Payment.objects.filter(
                paymentDate__range=[seven_days_ago, today],
                isDeleted=False,
                ownerID_id=owner_id,
            )
            .values("paymentDate")  # directly group by date
            .annotate(total=Sum("paymentAmount"))
            .order_by("paymentDate")
        )
    else:
        payments_today = (
            Payment.objects.filter(
                paymentDate=today,
                isDeleted=False,
                ownerID_id=owner_id,
                addedByID__userID_id=request.user.pk,
            ).aggregate(total=Sum("paymentAmount"))["total"]
            or 0
        )
        jars_in = (
            JarCounter.objects.filter(
                date=today,
                ownerID_id=owner_id,
                isDeleted=False,
                addedByID__userID_id=request.user.pk,
            ).aggregate(total=Sum("inJar"))["total"]
            or 0
        )
        jars_out = (
            JarCounter.objects.filter(
                date=today,
                ownerID_id=owner_id,
                isDeleted=False,
                addedByID__userID_id=request.user.pk,
            ).aggregate(total=Sum("outJar"))["total"]
            or 0
        )
        total_expense = (
            Expense.objects.filter(
                isDeleted=False,
                ownerID_id=owner_id,
                expenseDate=today,
                staffID__userID_id=request.user.pk,
            ).aggregate(total=Sum("expenseAmount"))["total"]
            or 0
        )
        total_sales = (
            Sales.objects.filter(
                isDeleted=False,
                ownerID_id=owner_id,
                saleDate=today,
                addedByID__userID_id=request.user.pk,
            ).aggregate(total=Sum("totalAmount"))["total"]
            or 0
        )
        total_customers = 0
        total_staff = 0
        total_suppliers = 0
        total_locations = 0

        today = timezone.now().date()
        seven_days_ago = today - datetime.timedelta(
            days=6
        )  # last 7 days including today

        # Get sales grouped by date
        sales_data = (
            Sales.objects.filter(
                saleDate__range=[seven_days_ago, today],
                isDeleted=False,
                ownerID_id=owner_id,
            )
            .values("saleDate")  # directly group by date
            .annotate(total=Sum("totalAmountAfterTax"))
            .order_by("saleDate")
        )
        # Get sales grouped by date
        payment_data = (
            Payment.objects.filter(
                paymentDate__range=[seven_days_ago, today],
                isDeleted=False,
                ownerID_id=owner_id,
            )
            .values("paymentDate")  # directly group by date
            .annotate(total=Sum("paymentAmount"))
            .order_by("paymentDate")
        )

    # Convert to dict for quick lookup
    sales_dict = {entry["saleDate"]: entry["total"] for entry in sales_data}

    final_dates = [(seven_days_ago + datetime.timedelta(days=i)) for i in range(7)]
    sales_date = [d.strftime("%b %d") for d in final_dates]
    sales_totals_by_date = [sales_dict.get(d, 0) for d in final_dates]

    # Convert to dict for quick lookup
    payment_dict = {entry["paymentDate"]: entry["total"] for entry in payment_data}
    payment_totals_by_date = [payment_dict.get(d, 0) for d in final_dates]

    context = {
        "payments_today": payments_today,
        "jars_in": int(jars_in),
        "jars_out": int(jars_out),
        "total_expense": total_expense,
        "total_sales": total_sales,
        "total_customers": total_customers,
        "total_staff": total_staff,
        "total_suppliers": total_suppliers,
        "sales_date": json.dumps(sales_date),  # JSON-safe
        "sales_totals_by_date": json.dumps(sales_totals_by_date),
        "total_locations": total_locations,
        "payment_totals_by_date": json.dumps(payment_totals_by_date),
    }
    return render(request, "wmaApp/dashboard.html", context)


def admin_home(request):
    return render(request, "admin_home.html")


@check_groups("Owner", "Manager", "Admin")
def manage_staff(request):
    logger.info("Manage staff called")
    owner_id = get_owner_id(request)
    groups = UserGroup.objects.filter(isDeleted=False, ownerID_id=owner_id)

    context = {"groups": groups}
    return render(request, "wmaApp/staff/manage_staff.html", context)


@check_groups("Owner", "Manager", "Admin", "Driver")
def manage_customer(request):
    logger.info("Manage customer called")
    location = Location.objects.filter(
        isDeleted=False, ownerID_id=get_owner_id(request)
    )

    context = {"locations": location}
    return render(request, "wmaApp/customer/manage_customer.html", context)


@check_groups("Owner", "Manager", "Admin")
def manage_supplier(request):
    return render(request, "wmaApp/manage_supplier.html")


@check_groups("Owner", "Manager", "Admin", "Driver")
def manage_location(request):
    logger.info("Manage location called")
    return render(request, "wmaApp/location/manage_locations.html")


@check_groups("Owner", "Manager", "Admin", "Driver")
def manage_orders(request):
    return render(request, "wmaApp/manage_orders.html")


@check_groups("Owner", "Manager", "Admin", "Driver")
def manage_profile(request):
    return render(request, "wmaApp/profile/manage_profile.html")


@check_groups("Owner", "Manager", "Admin")
def manage_expense_group(request):
    logger.info("Manage expense group called")
    return render(request, "wmaApp/expense_group/manage_expense_group.html")


@check_groups("Owner", "Manager", "Admin")
def manage_category(request):
    logger.info("Manage category called")
    return render(request, "wmaApp/inventory/manage_category.html")


@check_groups("Owner", "Manager", "Admin")
def manage_unit(request):
    logger.info("Manage unit called")
    return render(request, "wmaApp/inventory/manage_units.html")


@check_groups("Owner", "Manager", "Admin")
def manage_hsn_and_tax(request):
    logger.info("Manage HSN and Tax called")
    return render(request, "wmaApp/inventory/manage_tax_and_hsn.html")


@check_groups("Owner", "Manager", "Admin")
def manage_product(request):
    logger.info("Manage product called")
    categories = Category.objects.filter(
        isDeleted=False, ownerID_id=get_owner_id(request)
    )
    taxs = TaxAndHsn.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))
    units = Unit.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))

    context = {"categories": categories, "taxs": taxs, "units": units}

    return render(request, "wmaApp/inventory/manage_products.html", context)


@check_groups("Owner", "Manager", "Admin", "Driver")
def add_sale(request):
    logger.info("Add sale called")
    return render(request, "wmaApp/sales/add_sales.html")


@check_groups("Owner", "Manager", "Admin", "Driver")
def sales_list(request):
    logger.info("Sales list called")
    staffs = StaffUser.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))
    context = {"staffs": staffs}
    return render(request, "wmaApp/sales/sales_list.html", context)


@check_groups("Owner", "Manager", "Admin")
def edit_sale(request, id=None):
    logger.info("Edit sale called")
    object = get_object_or_404(
        Sales, pk=id, isDeleted=False, ownerID_id=get_owner_id(request)
    )
    products = SaleProduct.objects.filter(
        isDeleted=False, ownerID_id=get_owner_id(request), salesID_id=object.id
    )

    context = {"object": object, "products": products}
    return render(request, "wmaApp/sales/edit_sales.html", context)


@check_groups("Owner", "Manager", "Admin")
def detail_sale(request, id=None):
    logger.info("Detail sale called")
    object = get_object_or_404(
        Sales, pk=id, isDeleted=False, ownerID_id=get_owner_id(request)
    )
    products = SaleProduct.objects.filter(
        isDeleted=False, ownerID_id=get_owner_id(request), salesID_id=object.id
    )

    context = {"object": object, "products": products}
    return render(request, "wmaApp/sales/sales_detail.html", context)


@check_groups("Owner", "Manager", "Admin", "Driver")
def manage_expense(request):
    logger.info("Manage expense called")
    instances = ExpenseGroup.objects.filter(
        isDeleted=False, ownerID_id=get_owner_id(request)
    )
    context = {"instances": instances}

    return render(request, "wmaApp/expenditure/manage_expenditure.html", context)


@check_groups("Owner", "Manager", "Admin", "Driver")
def manage_jars(request):
    logger.info("Manage jars is called")
    return render(
        request,
        "wmaApp/jars/manage_jars.html",
    )


@check_groups("Owner", "Manager", "Admin", "Driver")
def manage_payments(request):
    logger.info("Manage payments is called")
    return render(
        request,
        "wmaApp/payments/manage_payments.html",
    )

@check_groups("Owner", "Manager", "Admin", "Driver")
def my_profile(request):
    try:
        instance = StaffUser.objects.select_related("userID").get(userID=request.user)
    except StaffUser.DoesNotExist:
        instance = get_object_or_404(
            Owner.objects.select_related("userID"), userID=request.user
        )

    return render(request, "wmaApp/profile/my_profile.html", {"instance": instance})

@check_groups("Owner", "Manager", "Admin", "Driver")
def customer_ledger(request, id=None):
    logger.info("Customer Ledger called with id: " + str(id))
    object = get_object_or_404(
        Customer, pk=id, isDeleted=False, ownerID_id=get_owner_id(request)
    )

    last_entry = CustomerLedger.objects.filter(
        customerID_id=id, isDeleted=False, ownerID_id=get_owner_id(request)
    ).last()
    if last_entry:
        running_balance = last_entry.balance
    else:
        running_balance = 0
    context = {"object": object, "balance": running_balance}
    return render(request, "wmaApp/customer/customer_ledger.html", context)


@check_groups("Owner", "Manager", "Admin", "Driver")
def reports(request):
    logger.info("Reports called")
    owner_id = get_owner_id(request)
    locations = Location.objects.filter(ownerID_id=owner_id, isDeleted=False).order_by(
        "name"
    )
    context = {"locations": locations}
    return render(request, "wmaApp/reports/reports.html", context)


# booking
@check_groups("Owner", "Manager", "Admin", "Driver")
def booking_list(request):
    logger.info("Booking list called")
    staffs = StaffUser.objects.filter(isDeleted=False, ownerID_id=get_owner_id(request))
    context = {"staffs": staffs}
    return render(request, "wmaApp/booking/booking_list.html", context)


@check_groups("Owner", "Manager", "Admin")
def edit_booking(request, id=None):
    logger.info("Edit booking called")
    object = get_object_or_404(
        AdvanceOrder, pk=id, isDeleted=False, ownerID_id=get_owner_id(request)
    )
    products = AdvanceOrderProduct.objects.filter(
        isDeleted=False, ownerID_id=get_owner_id(request), orderID_id=object.id
    )

    context = {"object": object, "products": products}
    return render(request, "wmaApp/booking/edit_booking.html", context)


@check_groups("Owner", "Manager", "Admin")
def detail_booking(request, id=None):
    logger.info("Detail booking called")
    object = get_object_or_404(
        AdvanceOrder, pk=id, isDeleted=False, ownerID_id=get_owner_id(request)
    )
    products = AdvanceOrderProduct.objects.filter(
        isDeleted=False, ownerID_id=get_owner_id(request), orderID_id=object.id
    )

    context = {"object": object, "products": products}
    return render(request, "wmaApp/booking/booking_detail.html", context)


@check_groups("Owner", "Manager", "Admin", "Driver")
def driver_jar_allocation(request):
    drivers = StaffUser.objects.filter(
        isDeleted=False,
        ownerID_id=get_owner_id(request),
        groupID__name__icontains="Driver",
    )
    logger.info("Driver jar allocation called")
    context = {"drivers": drivers}
    return render(request, "wmaApp/driver_jar_allocation/jar_allocation.html", context)


@check_groups("Owner", "Manager", "Admin", "Driver")
def my_jar_allocations(request):
    logger.info("Driver wise jar allocation called")
    return render(request, "wmaApp/driver_jar_allocation/driver_jar_allocation.html")
