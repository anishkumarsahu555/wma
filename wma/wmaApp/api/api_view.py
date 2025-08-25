from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User, Group
from django_datatables_view.base_datatable_view import BaseDatatableView

from utils.custom_response import SuccessResponse, ErrorResponse
from utils.get_owner_detail import get_owner_id
from utils.json_validator import validate_input
from wmaApp.models import *
from utils.logger import logger

# ---------------------------- staff user api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name','profile_pic','email','password','address','phone','group','is_active' ])
@transaction.atomic
def add_staff_api(request):
    data = request.POST.dict()
    try:
        profile_pic = request.FILES.get('profile_pic')
        # Get the UserGroup instance
        try:
            user_group = UserGroup.objects.get(name=data['group'], isDeleted=False)
        except UserGroup.DoesNotExist:
            logger.error(f"UserGroup '{data['group']}' does not exist")
            return ErrorResponse(f"UserGroup '{data['group']}' does not exist").to_json_response()
            
        staff = StaffUser(
            name=data['name'],
            password=data['password'],
            email=data.get('email', ''),
            phone=data['phone'],
            groupID=user_group,  # Assign the UserGroup instance
            profile_pic=profile_pic,
            address=data.get('address', ''),
            isActive=data.get('is_active', 'active').lower() == 'active',
            startDate=datetime.today().now(),
            ownerID_id=get_owner_id(request),
        )
        username = 'USER' + get_random_string(length=6, allowed_chars='1234567890')
        while User.objects.select_related().filter(username__exact=username).count() > 0:
            username = 'USER' + get_random_string(length=6, allowed_chars='1234567890')
        else:
            new_user = User()
            new_user.username = username
            new_user.set_password(data['password'])
            new_user.save()
            staff.username = username
            staff.userID = new_user
            staff.save()
            if not staff.isActive:
                new_user.is_active = False
                new_user.save()

            try:
                g = Group.objects.get(name=data['group'])
                g.user_set.add(new_user.pk)
                g.save()

            except:
                g = Group()
                g.name = data['group']
                g.save()
                g.user_set.add(new_user.pk)
                g.save()
        logger.info("Staff user created successfully")
        return SuccessResponse("Staff user created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating staff user: {e}")
        return ErrorResponse("Unable to add new staff. Please try again").to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['id','name','email','password','address','phone','group','is_active' ])
@transaction.atomic
def update_staff_api(request):
    data = request.POST.dict()
    try:
        # Get the UserGroup instance
        try:
            user_group = UserGroup.objects.get(name=data['group'], isDeleted=False)
        except UserGroup.DoesNotExist:
            logger.error(f"UserGroup '{data['group']}' does not exist")
            return ErrorResponse(f"UserGroup '{data['group']}' does not exist").to_json_response()
        try:
            staff = StaffUser.objects.get(pk=data['id'], isDeleted=False)
            staff.name = data['name']
            staff.email = data.get('email', '')
            staff.groupID = user_group
            staff.address = data.get('address', '')
            staff.isActive = data.get('is_active', 'active').lower() == 'active'
            staff.password = data['password']
            staff.phone = data['phone']
            staff.save()


            new_user = User.objects.get(id=staff.userID.pk)
            new_user.set_password(data['password'])

            if not staff.isActive:
                new_user.is_active = False
            else:
                new_user.is_active = True
            new_user.save()
            new_user.groups.clear()

            # Add user to group
            group, created = Group.objects.get_or_create(name=data['group'])
            group.user_set.add(new_user)
            group.save()
            logger.info("Staff user updated successfully")
            return SuccessResponse("Staff user updated successfully").to_json_response()
        except StaffUser.DoesNotExist:
            logger.error(f"Staff user with ID '{data['id']}' not found")
            return ErrorResponse("Staff user does not exist").to_json_response()
    except Exception as e:
        logger.error(f"Error while updating staff user: {e}")
        return ErrorResponse("Unable to update staff. Please try again").to_json_response()



class StaffUserListJson(BaseDatatableView):
    order_columns = ['profile_pic', 'name', 'username', 'password', 'groupID', 'phone', 'address',
                     'isActive', 'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return StaffUser.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(username__icontains=search)
                | Q(groupID__icontains=search) | Q(phone__icontains=search)
                | Q(address__icontains=search) | Q(isActive__icontains=search)
                | Q(dateCreated__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            images = '<img class="ui avatar image" src="{}">'.format(item.profile_pic.thumb.url)
            if 'Owner' or 'Manager' in self.request.user.groups.values_list('name', flat=True):
                action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),
                username = item.username
                password = item.password
            else:
                action = '''<div class="ui tiny label">
                  Denied
                </div>'''
                username = "*********"
                password = "*********"

            json_data.append([
                images,  # escape HTML for security reasons
                escape(item.name),
                username,
                password,
                escape(item.groupID.name),
                escape(item.phone),
                escape(item.address),
                escape(item.isActive),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@require_http_methods(["GET"])
@validate_input(['id'])
def get_staff_detail(request):
    try:
        staff_id = request.GET.get('id')
        # Get single staff user
        try:
            staff = StaffUser.objects.get(id=staff_id, isDeleted=False)
            data = {
                'id': staff.id,
                'name': staff.name,
                'email': staff.email,
                'password':staff.password ,
                'group': staff.groupID.name,
                'phone': staff.phone,
                'address': staff.address,
                'isActive': 'Active' if staff.isActive else 'In-Active',
                'profile_pic': staff.profile_pic.url,


            }
            logger.info("Staff user fetched successfully")
            return SuccessResponse("Staff user fetched successfully", data=data).to_json_response()
        except StaffUser.DoesNotExist:
            logger.error(f"Staff user with ID '{staff_id}' not found")
            return ErrorResponse("Staff user not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching staff user: {e}")
        return ErrorResponse( 'Server Error', status_code=500).to_json_response()


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_staff(request):

    staff_id = request.POST.get("id")
    try:
        try:
            staff = StaffUser.objects.get(id=staff_id, isDeleted=False)
        except StaffUser.DoesNotExist:
            logger.error(f"Staff user not found")
            return ErrorResponse("Staff user not found", status_code=404).to_json_response()

        # Soft delete
        staff.isDeleted = True
        staff.isActive = False
        staff.save()

        # Also deactivate the associated user
        if staff.userID:
            staff.userID.is_active = False
            staff.userID.save()
        logger.info("Staff user deleted successfully")
        return SuccessResponse("Staff user deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting staff user: {e}")
        return ErrorResponse(str(e), status_code=500).to_json_response()


# ---------------------------- Location api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name' ])
@transaction.atomic
def add_location_api(request):
    data = request.POST.dict()
    try:
        # Check if location with same name already exists
        if Location.objects.filter(
                name__iexact=data['name'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
        ).exists():
            logger.error(f"Location with name '{data['name']}' already exists")
            return ErrorResponse("A location with this name already exists", status_code=400).to_json_response()
        obj = Location(
            name=data['name'],
            ownerID_id=get_owner_id(request),
        )
        obj.save()
        logger.info("Location created successfully")
        return SuccessResponse("Location created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating location: {e}")
        return ErrorResponse("Unable to add new location. Please try again").to_json_response()

class LocationListJson(BaseDatatableView):
    order_columns = [ 'name',  'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Location.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(dateCreated__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            if 'Owner' or 'Manager' in self.request.user.groups.values_list('name', flat=True):
                action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            else:
                action = '''<div class="ui tiny label">
                  Denied
                </div>'''


            json_data.append([
                escape(item.name),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_location_api(request):

    obj_id = request.POST.get("id")
    try:
        try:
            obj = Location.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
        except Location.DoesNotExist:
            logger.error(f"Location not found")
            return ErrorResponse("Location not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()

        logger.info("Location deleted successfully")
        return SuccessResponse("Location deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting Location: {e}")
        return ErrorResponse(str(e), status_code=500).to_json_response()



@require_http_methods(["GET"])
@validate_input(['id'])
def get_location_detail(request):
    try:
        obj_id = request.GET.get('id')
        # Get single staff user
        try:
            obj = Location.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
            data = {
                'id': obj.id,
                'name': obj.name,
            }
            logger.info("Location fetched successfully")
            return SuccessResponse("Location fetched successfully", data=data).to_json_response()
        except Location.DoesNotExist:
            logger.error(f"Location with ID '{obj_id}' not found")
            return ErrorResponse("Location not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching Location: {e}")
        return ErrorResponse( 'Server Error', status_code=500).to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name', 'id' ])
@transaction.atomic
def update_location_api(request):
    data = request.POST.dict()
    try:
        # Check if location exists and belongs to the owner
        try:
            obj = Location.objects.get(
                id=data['id'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
            )
        except Location.DoesNotExist:
            logger.error(f"Location with ID {data["id"]}' not found")
            return ErrorResponse("Location not found", status_code=404).to_json_response()

        # Check if another location with the same name already exists (excluding current location)
        if (Location.objects
                .filter(
            name__iexact=data['name'],
            ownerID_id=get_owner_id(request),
            isDeleted=False
        )
                .exclude(id=data['id'])
                .exists()):
            logger.error(f"Another location with name '{data['name']}' already exists")
            return ErrorResponse("A location with this name already exists", status_code=400).to_json_response()

        # Update the location
        obj.name = data['name']
        obj.save()

        logger.info(f"Location '{data['id']}' updated successfully")
        return SuccessResponse("Location updated successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while updating location: {str(e)}")
        return ErrorResponse("Unable to update location. Please try again", status_code=500).to_json_response()



# ---------------------------- Manage Expense Group api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name' ])
@transaction.atomic
def add_expense_group_api(request):
    data = request.POST.dict()
    try:
        # Check if Expense Group with same name already exists
        if ExpenseGroup.objects.filter(
                name__iexact=data['name'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
        ).exists():
            logger.error(f"Expense Group with name '{data['name']}' already exists")
            return ErrorResponse("A expense group with this name already exists", status_code=400).to_json_response()
        obj = ExpenseGroup(
            name=data['name'],
            ownerID_id=get_owner_id(request),
        )
        obj.save()
        logger.info("Expense Group created successfully")
        return SuccessResponse("Expense Group created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating expense group: {e}")
        return ErrorResponse("Unable to add new expense group. Please try again").to_json_response()

class ExpenseGroupListJson(BaseDatatableView):
    order_columns = [ 'name',  'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return ExpenseGroup.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(dateCreated__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            if 'Owner' or 'Manager' in self.request.user.groups.values_list('name', flat=True):
                action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            else:
                action = '''<div class="ui tiny label">
                  Denied
                </div>'''


            json_data.append([
                escape(item.name),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_expense_group_api(request):

    obj_id = request.POST.get("id")
    try:
        try:
            obj = ExpenseGroup.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
        except ExpenseGroup.DoesNotExist:
            logger.error(f"Expense Group not found")
            return ErrorResponse("Expense Group not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()

        logger.info("Expense Group deleted successfully")
        return SuccessResponse("Expense Group deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting Expense Group: {e}")
        return ErrorResponse(str(e), status_code=500).to_json_response()



@require_http_methods(["GET"])
@validate_input(['id'])
def get_expense_group_detail(request):
    try:
        obj_id = request.GET.get('id')
        # Get single staff user
        try:
            obj = ExpenseGroup.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
            data = {
                'id': obj.id,
                'name': obj.name,
            }
            logger.info("Expense Group fetched successfully")
            return SuccessResponse("Expense Group fetched successfully", data=data).to_json_response()
        except ExpenseGroup.DoesNotExist:
            logger.error(f"Expense Group with ID '{obj_id}' not found")
            return ErrorResponse("Expense Group not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching Expense Group: {e}")
        return ErrorResponse( 'Unable to fetch expense group. Please try again', status_code=500).to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name', 'id' ])
@transaction.atomic
def update_expense_group_api(request):
    data = request.POST.dict()
    try:
        # Check if Expense Group exists and belongs to the owner
        try:
            obj = ExpenseGroup.objects.get(
                id=data['id'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
            )
        except ExpenseGroup.DoesNotExist:
            logger.error(f"Expense Group with ID {data["id"]}' not found")
            return ErrorResponse("Expense Group not found", status_code=404).to_json_response()

        # Check if another Expense Group with the same name already exists (excluding current Expense Group)
        if (ExpenseGroup.objects
                .filter(
            name__iexact=data['name'],
            ownerID_id=get_owner_id(request),
            isDeleted=False
        )
                .exclude(id=data['id'])
                .exists()):
            logger.error(f"Another expense group with name '{data['name']}' already exists")
            return ErrorResponse("A expense group with this name already exists", status_code=400).to_json_response()

        # Update the Expense Group
        obj.name = data['name']
        obj.save()

        logger.info(f"Expense Group '{data['id']}' updated successfully")
        return SuccessResponse("Expense Group updated successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while updating expense group: {str(e)}")
        return ErrorResponse("Unable to update expense group. Please try again", status_code=500).to_json_response()

# ---------------------------- Customer user api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name','profile_pic','email','location','address','phone' ])
@transaction.atomic
def add_customer_api(request):
    data = request.POST.dict()
    try:
        profile_pic = request.FILES.get('profile_pic')
        try:
            location = Location.objects.get(id=data['location'], isDeleted=False, ownerID_id=get_owner_id(request))
        except:
            logger.error(f"Location not found")
            return ErrorResponse("Location not found", status_code=404).to_json_response()

        obj = Customer(
            name=data['name'],
            email=data.get('email', ''),
            phone=data['phone'],
            locationID=location,  # Assign the UserGroup instance
            profile_pic=profile_pic,
            address=data.get('address', ''),
            addedDate=datetime.today().now(),
            ownerID_id=get_owner_id(request),
        )
        username = 'CUS' + get_random_string(length=8, allowed_chars='1234567890')
        password = get_random_string(length=8, allowed_chars='1234567890')
        while User.objects.select_related().filter(username__exact=username).count() > 0:
            username = 'CUS' + get_random_string(length=8, allowed_chars='1234567890')
        else:
            new_user = User()
            new_user.username = username
            new_user.set_password(password)
            new_user.save()
            obj.username = username
            obj.userID = new_user
            obj.save()
            customer_count = Customer.objects.select_related().filter(ownerID_id=get_owner_id(request)).count()
            obj.customerId = 'CID' + str(customer_count).zfill(8)
            obj.save()
            # Add user to group
            group, created = Group.objects.get_or_create(name='Customer')
            group.user_set.add(new_user)
            group.save()
        logger.info("Customer user created successfully")
        return SuccessResponse("Customer user created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating Customer user: {e}")
        return ErrorResponse("Unable to add new Customer. Please try again").to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['id','name','email','location','address','phone' ])
@transaction.atomic
def update_customer_api(request):
    data = request.POST.dict()
    try:
        # Get the Location instance
        try:
            loc = Location.objects.get(id=data['location'], isDeleted=False, ownerID_id=get_owner_id(request))
        except Location.DoesNotExist:
            logger.error(f"Location '{data['location']}' does not exist")
            return ErrorResponse(f"Location does not exist").to_json_response()
        try:
            obj = Customer.objects.get(pk=data['id'], isDeleted=False, ownerID_id=get_owner_id(request))

            obj.name = data['name']
            obj.email = data.get('email', '')
            obj.locationID = loc
            obj.address = data.get('address', '')
            obj.phone = data['phone']
            obj.save()

            logger.info("Customer user updated successfully")
            return SuccessResponse("Customer user updated successfully").to_json_response()
        except Customer.DoesNotExist:
            logger.error(f"Customer user with ID '{data['id']}' not found")
            return ErrorResponse("Customer user does not exist").to_json_response()
    except Exception as e:
        logger.error(f"Error while updating Customer user: {e}")
        return ErrorResponse("Unable to update Customer. Please try again").to_json_response()



class CustomerListJson(BaseDatatableView):
    order_columns = ['profile_pic', 'customerId','name',  'locationID', 'phone', 'address', 'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Customer.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(customerId__icontains=search)
                | Q(locationID__icontains=search) | Q(phone__icontains=search)
                | Q(address__icontains=search)
                | Q(dateCreated__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            images = '<img class="ui avatar image" src="{}">'.format(item.profile_pic.thumb.url)
            if 'Owner' or 'Manager' in self.request.user.groups.values_list('name', flat=True):
                action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),
            else:
                action = '''<div class="ui tiny label">
                  Denied
                </div>'''

            json_data.append([
                images,  # escape HTML for security reasons
                escape(item.customerId),
                escape(item.name),
                escape(item.locationID.name),
                escape(item.phone),
                escape(item.address),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])
        return json_data


@require_http_methods(["GET"])
@validate_input(['id'])
def get_customer_detail(request):
    try:
        obj_id = request.GET.get('id')
        # Get single customer user
        try:
            obj = Customer.objects.get(id=obj_id, isDeleted=False)
            data = {
                'id': obj.id,
                'name': obj.name,
                'email': obj.email,
                'location': obj.locationID.id,
                'phone': obj.phone,
                'address': obj.address,
                'profile_pic': obj.profile_pic.url,


            }
            logger.info("Customer user fetched successfully")
            return SuccessResponse("Customer user fetched successfully", data=data).to_json_response()
        except Customer.DoesNotExist:
            logger.error(f"Customer user with ID '{obj_id}' not found")
            return ErrorResponse("Customer user not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching Customer user: {e}")
        return ErrorResponse( 'Unable to fetch Customer user. Please try again', status_code=500).to_json_response()


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_customer(request):

    id = request.POST.get("id")
    try:
        try:
            obj = Customer.objects.get(id=id, isDeleted=False)
        except Customer.DoesNotExist:
            logger.error(f"Customer user not found")
            return ErrorResponse("Customer user not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.isActive = False
        obj.save()

        # Also deactivate the associated user
        if obj.userID:
            obj.userID.is_active = False
            obj.userID.save()
        logger.info("Customer user deleted successfully")
        return SuccessResponse("Customer user deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting Customer user: {e}")
        return ErrorResponse(f"Unable to delete Customer user. Please try again", status_code=500).to_json_response()

# ---------------------------- Category api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name' ])
@transaction.atomic
def add_category_api(request):
    data = request.POST.dict()
    try:
        # Check if location with same name already exists
        if Category.objects.filter(
                name__iexact=data['name'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
        ).exists():
            logger.error(f"Category with name '{data['name']}' already exists")
            return ErrorResponse("A category with this name already exists", status_code=400).to_json_response()
        obj = Category(
            name=data['name'],
            ownerID_id=get_owner_id(request),
        )
        obj.save()
        logger.info("Category created successfully")
        return SuccessResponse("Category created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating Category: {e}")
        return ErrorResponse("Unable to add new Category. Please try again").to_json_response()

class CategoryListJson(BaseDatatableView):
    order_columns = [ 'name',  'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Category.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(dateCreated__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            if 'Owner' or 'Manager' in self.request.user.groups.values_list('name', flat=True):
                action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            else:
                action = '''<div class="ui tiny label">
                  Denied
                </div>'''


            json_data.append([
                escape(item.name),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_category_api(request):

    obj_id = request.POST.get("id")
    try:
        try:
            obj = Category.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
        except Category.DoesNotExist:
            logger.error(f"Category not found")
            return ErrorResponse("Category not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()

        logger.info("Category deleted successfully")
        return SuccessResponse("Category deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting Category: {e}")
        return ErrorResponse("Error while deleting Category", status_code=500).to_json_response()



@require_http_methods(["GET"])
@validate_input(['id'])
def get_category_detail(request):
    try:
        obj_id = request.GET.get('id')
        # Get single staff user
        try:
            obj = Category.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
            data = {
                'id': obj.id,
                'name': obj.name,
            }
            logger.info("Category fetched successfully")
            return SuccessResponse("Category fetched successfully", data=data).to_json_response()
        except Category.DoesNotExist:
            logger.error(f"Category with ID '{obj_id}' not found")
            return ErrorResponse("Category not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching Category: {e}")
        return ErrorResponse( 'Server Error', status_code=500).to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name', 'id' ])
@transaction.atomic
def update_category_api(request):
    data = request.POST.dict()
    try:
        # Check if Category exists and belongs to the owner
        try:
            obj = Category.objects.get(
                id=data['id'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
            )
        except Category.DoesNotExist:
            logger.error(f"Category with ID {data["id"]}' not found")
            return ErrorResponse("Category not found", status_code=404).to_json_response()

        # Check if another Category with the same name already exists (excluding current Category)
        if (Category.objects
                .filter(
            name__iexact=data['name'],
            ownerID_id=get_owner_id(request),
            isDeleted=False
        )
                .exclude(id=data['id'])
                .exists()):
            logger.error(f"Another Category with name '{data['name']}' already exists")
            return ErrorResponse("A Category with this name already exists", status_code=400).to_json_response()

        # Update the location
        obj.name = data['name']
        obj.save()

        logger.info(f"Category '{data['id']}' updated successfully")
        return SuccessResponse("Category updated successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while updating Category: {str(e)}")
        return ErrorResponse("Unable to update Category. Please try again", status_code=500).to_json_response()


# ---------------------------- Unit api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name' ])
@transaction.atomic
def add_unit_api(request):
    data = request.POST.dict()
    try:
        # Check if location with same name already exists
        if Unit.objects.filter(
                name__iexact=data['name'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
        ).exists():
            logger.error(f"Unit with name '{data['name']}' already exists")
            return ErrorResponse("A Unit with this name already exists", status_code=400).to_json_response()
        obj = Unit(
            name=data['name'],
            ownerID_id=get_owner_id(request),
        )
        obj.save()
        logger.info("Unit created successfully")
        return SuccessResponse("Unit created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating Unit: {e}")
        return ErrorResponse("Unable to add new Unit. Please try again").to_json_response()

class UnitListJson(BaseDatatableView):
    order_columns = [ 'name',  'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Unit.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(dateCreated__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            if 'Owner' or 'Manager' in self.request.user.groups.values_list('name', flat=True):
                action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            else:
                action = '''<div class="ui tiny label">
                  Denied
                </div>'''


            json_data.append([
                escape(item.name),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_unit_api(request):

    obj_id = request.POST.get("id")
    try:
        try:
            obj = Unit.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
        except Unit.DoesNotExist:
            logger.error(f"Unit not found")
            return ErrorResponse("Unit not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()

        logger.info("Unit deleted successfully")
        return SuccessResponse("Unit deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting Unit: {e}")
        return ErrorResponse("Error while deleting Unit", status_code=500).to_json_response()



@require_http_methods(["GET"])
@validate_input(['id'])
def get_unit_detail(request):
    try:
        obj_id = request.GET.get('id')
        try:
            obj = Unit.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
            data = {
                'id': obj.id,
                'name': obj.name,
            }
            logger.info("Unit fetched successfully")
            return SuccessResponse("Unit fetched successfully", data=data).to_json_response()
        except Unit.DoesNotExist:
            logger.error(f"Unit with ID '{obj_id}' not found")
            return ErrorResponse("Unit not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching Unit: {e}")
        return ErrorResponse( 'Server Error', status_code=500).to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name', 'id' ])
@transaction.atomic
def update_unit_api(request):
    data = request.POST.dict()
    try:
        try:
            obj = Unit.objects.get(
                id=data['id'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
            )
        except Unit.DoesNotExist:
            logger.error(f"Unit with ID {data["id"]}' not found")
            return ErrorResponse("Unit not found", status_code=404).to_json_response()

        if (Unit.objects
                .filter(
            name__iexact=data['name'],
            ownerID_id=get_owner_id(request),
            isDeleted=False
        )
                .exclude(id=data['id'])
                .exists()):
            logger.error(f"Another Unit with name '{data['name']}' already exists")
            return ErrorResponse("A Unit with this name already exists", status_code=400).to_json_response()

        # Update the location
        obj.name = data['name']
        obj.save()

        logger.info(f"Unit '{data['id']}' updated successfully")
        return SuccessResponse("Unit updated successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while updating Unit: {str(e)}")
        return ErrorResponse("Unable to update Unit. Please try again", status_code=500).to_json_response()

