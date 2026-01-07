
from tkinter.constants import E
from django.db.models.functions import Exp
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from weasyprint import HTML, CSS
from datetime import datetime, timedelta
from wmaApp.models import Sales, Location, JarCounter, Expense, Payment
from wmaApp.api.api_view import get_owner_id
from django.db.models import Sum
from utils.logger import logger


@csrf_exempt
def download_report_pdf(request):
    cDate = request.POST.get('startDate')
    eDate = request.POST.get('endDate')
    location = request.POST.get('location')
    reportType = request.POST.get('reportType')
    owner_id = get_owner_id(request)
    startDate = datetime.strptime(cDate, '%d/%m/%Y')
    endDate = datetime.strptime(eDate, '%d/%m/%Y')

    match reportType:
        case 'Sales':
            return generate_sales_report_pdf(request, startDate, endDate, location, owner_id)
        case 'Jar':
            return generate_jar_report_pdf(request, startDate, endDate, location, owner_id)
        case 'Expense':
            return generate_expense_report_pdf(request, startDate, endDate, location, owner_id)  
        case 'Collection':
            return generate_collection_report_pdf(request, startDate, endDate, location, owner_id)  



def generate_sales_report_pdf(request, startDate, endDate, location, owner_id):
    logger.info("Generating sales report pdf for owner_id: %s", owner_id)
    if location == 'All':
        col = Sales.objects.select_related().filter(saleDate__range=(
            startDate.date(), endDate.date() + timedelta(days=1)),
            isDeleted__exact=False, ownerID_id=owner_id).order_by('addedByID__name')
    else:
        col = Sales.objects.select_related().filter(saleDate__range=(
            startDate.date(), endDate.date() + timedelta(days=1)),
            isDeleted__exact=False, customerID__locationID_id=int(location), ownerID_id=owner_id).order_by('addedByID__name')
    total = col.aggregate(Sum('totalAmountAfterTax'))
    totalAmountAfterTax = total['totalAmountAfterTax__sum'] or 0
    context = {
        'startDate': startDate,
        'endDate': endDate,
        'col': col,
        'location': 'All' if location == 'All' else Location.objects.get(id=location, ownerID_id=owner_id).name,
        'total': totalAmountAfterTax,
    }

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = "report.pdf"
    html = render_to_string("wmaApp/reports/salesPDF.html", context)

    HTML(string=html).write_pdf(response, stylesheets=[CSS(string='@page { size: A5; margin: .3cm ; }')])
    return response

def generate_jar_report_pdf(request, startDate, endDate, location, owner_id):
    logger.info("Generating jar report pdf for owner_id: %s", owner_id)
    if location == 'All':
        col = JarCounter.objects.select_related().filter(date__range=(
            startDate.date(), endDate.date() + timedelta(days=1)),
            isDeleted__exact=False, ownerID_id=owner_id).order_by('addedByID__name')
    else:
        col = JarCounter.objects.select_related().filter(date__range=(
            startDate.date(), endDate.date() + timedelta(days=1)),
            isDeleted__exact=False, customerID__locationID_id=int(location), ownerID_id=owner_id).order_by('addedByID__name')
    in_total = col.aggregate(Sum('inJar'))
    inJar = in_total['inJar__sum'] or 0
    out_total = col.aggregate(Sum('outJar'))
    outJar = out_total['outJar__sum'] or 0
    context = {
        'startDate': startDate,
        'endDate': endDate,
        'col': col,
        'location': 'All' if location == 'All' else Location.objects.get(id=location, ownerID_id=owner_id).name,
        'inJar': inJar,
        'outJar': outJar,
    }

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = "report.pdf"
    html = render_to_string("wmaApp/reports/jarPDF.html", context)

    HTML(string=html).write_pdf(response, stylesheets=[CSS(string='@page { size: A5; margin: .3cm ; }')])
    return response    

def generate_expense_report_pdf(request, startDate, endDate, location, owner_id):
    logger.info("Generating expense report pdf for owner_id: %s", owner_id)
    if location == 'All':
        col = Expense.objects.select_related().filter(expenseDate__range=(
            startDate.date(), endDate.date() + timedelta(days=1)),
            isDeleted__exact=False, ownerID_id=owner_id).order_by('-id')
    else:
        col = Expense.objects.select_related().filter(expenseDate__range=(
            startDate.date(), endDate.date() + timedelta(days=1)),
            isDeleted__exact=False, staffID__locationID_id=int(location), ownerID_id=owner_id).order_by('-id')
    total = col.aggregate(Sum('expenseAmount'))
    expenseAmount = total['expenseAmount__sum'] or 0
    context = {
        'startDate': startDate,
        'endDate': endDate,
        'col': col,
        'location': 'All' if location == 'All' else Location.objects.get(id=location, ownerID_id=owner_id).name,
        'total': expenseAmount,
    }

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = "report.pdf"
    html = render_to_string("wmaApp/reports/expensePDF.html", context)

    HTML(string=html).write_pdf(response, stylesheets=[CSS(string='@page { size: A5; margin: .3cm ; }')])
    return response



def generate_collection_report_pdf(request, startDate, endDate, location, owner_id):
    logger.info("Generating collection report pdf for owner_id: %s", owner_id)
    if location == 'All':
        col = Payment.objects.select_related().filter(paymentDate__range=(
            startDate.date(), endDate.date() + timedelta(days=1)),
            isDeleted__exact=False, ownerID_id=owner_id).order_by('-id')
    else:
        col = Payment.objects.select_related().filter(paymentDate__range=(
            startDate.date(), endDate.date() + timedelta(days=1)),
            isDeleted__exact=False, customerID__locationID_id=int(location), ownerID_id=owner_id).order_by('-id')
    total = col.aggregate(Sum('paymentAmount'))
    paymentAmount = total['paymentAmount__sum'] or 0
    context = {
        'startDate': startDate,
        'endDate': endDate,
        'col': col,
        'location': 'All' if location == 'All' else Location.objects.get(id=location, ownerID_id=owner_id).name,
        'total': paymentAmount,
    }

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = "report.pdf"
    html = render_to_string("wmaApp/reports/collectionPDF.html", context)

    HTML(string=html).write_pdf(response, stylesheets=[CSS(string='@page { size: A5; margin: .3cm ; }')])
    return response
