from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.core.cache import cache
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
    owner_id = get_owner_id(request)
    try:
        profile_pic = request.FILES.get('profile_pic')
        # Get the UserGroup instance
        try:
            user_group = UserGroup.objects.get(name=data['group'], isDeleted=False, ownerID_id=owner_id)
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
            ownerID_id=owner_id,
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
        return StaffUser.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

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
            staff = StaffUser.objects.get(id=staff_id, isDeleted=False, ownerID_id=get_owner_id(request))
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
            staff = StaffUser.objects.get(id=staff_id, isDeleted=False, ownerID_id=get_owner_id(request))
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
        owner_id = get_owner_id(request)
        profile_pic = request.FILES.get('profile_pic')
        try:
            location = Location.objects.get(id=data['location'], isDeleted=False, ownerID_id=owner_id)
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
            ownerID_id=owner_id,
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
            cache.delete(f'CustomerList{owner_id}')
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
        owner_id = get_owner_id(request)
        # Get the Location instance
        try:
            loc = Location.objects.get(id=data['location'], isDeleted=False, ownerID_id=owner_id)
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
            cache.delete(f'CustomerList{owner_id}')

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
        owner_id = get_owner_id(request)
        try:
            obj = Customer.objects.get(id=id, isDeleted=False, ownerID_id=owner_id)
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
        cache.delete(f'CustomerList{owner_id}')
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


# ---------------------------- HSN and Tax api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name', 'tax' ])
@transaction.atomic
def add_hsn_and_tax_api(request):
    data = request.POST.dict()
    try:
        if TaxAndHsn.objects.filter(
                hsn__iexact=data['name'],
                taxRate=data['tax'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
        ).exists():
            logger.error(f"Hsn with name '{data['name']}' and Tax rate '{data['tax']}' already exists")
            return ErrorResponse("A HSN with this detail already exists", status_code=400).to_json_response()
        obj = TaxAndHsn(
            hsn=data['name'],
            taxRate=data['tax'],
            ownerID_id=get_owner_id(request),
        )
        obj.save()
        logger.info("HSN Tax created successfully")
        return SuccessResponse("HSN Tax created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating HSN Tax: {e}")
        return ErrorResponse("Unable to add new HSN Tax. Please try again").to_json_response()

class HSNTAXListJson(BaseDatatableView):
    order_columns = [ 'name','taxRate',  'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return TaxAndHsn.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(hsn__icontains=search)
                | Q(taxRate__icontains=search)| Q(dateCreated__icontains=search)
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
                escape(item.hsn),
                escape(item.taxRate),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_hsn_and_tax_api(request):

    obj_id = request.POST.get("id")
    try:
        try:
            obj = TaxAndHsn.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
        except TaxAndHsn.DoesNotExist:
            logger.error(f"HSN Tax not found")
            return ErrorResponse("HSN Tax not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()

        logger.info("HSN Tax deleted successfully")
        return SuccessResponse("HSN Tax deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting HSN Tax: {e}")
        return ErrorResponse("Error while deleting HSN Tax", status_code=500).to_json_response()



@require_http_methods(["GET"])
@validate_input(['id'])
def get_hsn_and_tax_detail(request):
    try:
        obj_id = request.GET.get('id')
        try:
            obj = TaxAndHsn.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
            data = {
                'id': obj.id,
                'name': obj.hsn,
                'tax': obj.taxRate,
            }
            logger.info("HSN Tax fetched successfully")
            return SuccessResponse("HSN Tax fetched successfully", data=data).to_json_response()
        except TaxAndHsn.DoesNotExist:
            logger.error(f"HSN Tax with ID '{obj_id}' not found")
            return ErrorResponse("HSN Tax not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching HSN Tax: {e}")
        return ErrorResponse( 'Server Error', status_code=500).to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['name', 'id','tax' ])
@transaction.atomic
def update_hsn_and_tax_api(request):
    data = request.POST.dict()
    try:
        try:
            obj = TaxAndHsn.objects.get(
                id=data['id'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
            )
        except TaxAndHsn.DoesNotExist:
            logger.error(f"HSN Tax with ID {data["id"]}' not found")
            return ErrorResponse("HSN Tax not found", status_code=404).to_json_response()

        if (TaxAndHsn.objects
                .filter(
            hsn__iexact=data['name'],
            taxRate=data['tax'],
            ownerID_id=get_owner_id(request),
            isDeleted=False
        )
                .exclude(id=data['id'])
                .exists()):
            logger.error(f"Another HSN with name '{data['name']}' and Tax Rate '{data['tax']}'  already exists")
            return ErrorResponse("A HSN Tax with this name already exists", status_code=400).to_json_response()

        # Update the location
        obj.hsn = data['name']
        obj.taxRate = data['tax']
        obj.save()

        logger.info(f"HSN Tax '{data['id']}' updated successfully")
        return SuccessResponse("HSN Tax updated successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while updating HSN Tax: {str(e)}")
        return ErrorResponse("Unable to update HSN Tax. Please try again", status_code=500).to_json_response()


# ---------------------------- Product api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['product', 'tax', 'category', 'unit', 'rate', 'quantity', 'sellingPrice', 'description' ])
@transaction.atomic
def add_product_api(request):
    data = request.POST.dict()
    try:
        owner_id = get_owner_id(request)
        if Product.objects.filter(
                productName__iexact=data['product'],
                ownerID_id=owner_id,
                isDeleted=False
        ).exists():
            logger.error(f"Product with name '{data['product']}' already exists")
            return ErrorResponse("A HSN with this detail already exists", status_code=400).to_json_response()
        obj = Product(
            productName=data['product'],
            productDescription=data['description'],
            rate=data['rate'],
            quantity=data['quantity'],
            sp=data['sellingPrice'],
            taxID_id=data['tax'],
            categoryID_id=data['category'],
            unitID_id=data['unit'],
            ownerID_id=owner_id,
        )
        obj.save()
        cache.delete(f'ProductList{owner_id}')
        logger.info("Product created successfully")
        return SuccessResponse("Product created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating Product: {e}")
        return ErrorResponse("Unable to add new Product. Please try again").to_json_response()

class ProductListJson(BaseDatatableView):
    order_columns = [ 'productName','categoryID', 'rate','quantity', 'unitID', 'taxID', 'sp', 'productDescription',  'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Product.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(productName__icontains=search)
                |Q(categoryID__name__icontains=search)
                |Q(rate__icontains=search)
                |Q(quantity__icontains=search)
                |Q(unitID__name__icontains=search)
                |Q(taxID__hsn__icontains=search)
                |Q(sp__icontains=search)
                |Q(productDescription__icontains=search)
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
                escape(item.productName),
                escape(item.categoryID.name),
                escape(item.rate),
                escape(item.quantity),
                escape(item.unitID.name),
                escape(item.taxID.hsn) + ' - ' + escape(item.taxID.taxRate),
                escape(item.sp),
                escape(item.productDescription),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data

@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_product_api(request):
    owner_id = get_owner_id(request)
    obj_id = request.POST.get("id")
    try:
        try:
            obj = Product.objects.get(id=obj_id, isDeleted=False, ownerID_id=owner_id)
        except Product.DoesNotExist:
            logger.error(f"Product not found")
            return ErrorResponse("Product not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()
        cache.delete(f'ProductList{owner_id}')
        logger.info("Product deleted successfully")
        return SuccessResponse("Product deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting product: {e}")
        return ErrorResponse("Error while deleting product", status_code=500).to_json_response()



@require_http_methods(["GET"])
@validate_input(['id'])
def get_product_detail(request):
    try:
        obj_id = request.GET.get('id')
        try:
            obj = Product.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
            data = {
                'id': obj.id,
                'name': obj.productName,
                'description': obj.productDescription,
                'rate': obj.rate,
                'quantity': obj.quantity,
                'unit': obj.unitID.id,
                'tax': obj.taxID.id,
                'sellingPrice': obj.sp,
                'category': obj.categoryID.id,

            }
            logger.info("Product fetched successfully")
            return SuccessResponse("Product fetched successfully", data=data).to_json_response()
        except Product.DoesNotExist:
            logger.error(f"Product with ID '{obj_id}' not found")
            return ErrorResponse("Product not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching Product: {e}")
        return ErrorResponse( 'Server Error', status_code=500).to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['id', 'product', 'tax', 'category', 'unit', 'rate', 'quantity', 'sellingPrice', 'description'  ])
@transaction.atomic
def update_product_api(request):
    data = request.POST.dict()
    try:
        owner_id = get_owner_id(request)
        try:
            obj = Product.objects.get(
                id=data['id'],
                ownerID_id=owner_id,
                isDeleted=False
            )
        except Product.DoesNotExist:
            logger.error(f"Product with ID {data["id"]}' not found")
            return ErrorResponse("Product not found", status_code=404).to_json_response()

        if (Product.objects
                .filter(
            productName__iexact=data['product'],
            ownerID_id=owner_id,
            isDeleted=False
        )
                .exclude(id=data['id'])
                .exists()):
            logger.error(f"Another product with name '{data['product']}'  already exists")
            return ErrorResponse("A Product with this name already exists", status_code=400).to_json_response()

        # Update the location
        obj.productName=data['product']
        obj.productDescription=data['description']
        obj.rate=data['rate']
        obj.quantity=data['quantity']
        obj.sp=data['sellingPrice']
        obj.taxID_id=data['tax']
        obj.categoryID_id=data['category']
        obj.unitID_id=data['unit']
        obj.save()
        cache.delete(f'ProductList{owner_id}')
        logger.info(f"Product '{data['id']}' updated successfully")
        return SuccessResponse("Product updated successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while updating Product: {str(e)}")
        return ErrorResponse("Unable to update Product. Please try again", status_code=500).to_json_response()


# ------------------ Sales --------------------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['customer', 'saleDate', 'grandTotal', 'additionalCharge', 'tax', 'datas', 'subTotal'])
@transaction.atomic
def add_sales_api(request):
    data = request.POST.dict()
    try:
        owner_id = get_owner_id(request)
        obj = Sales(
            customerID_id=data['customer'],
            saleDate=datetime.strptime(data['saleDate'], '%d/%m/%Y'),
            totalAmount=data['subTotal'],
            totalTax=data['tax'],
            additionalCharge=data['additionalCharge'],
            totalAmountAfterTax=data['grandTotal'],
            ownerID_id=owner_id,
        )
        obj.save()
        obj.invoiceNumber = "S"+str(Sales.objects.filter(ownerID_id=owner_id).count()).zfill(8)
        obj.save()
        splited_receive_item = data['datas'].split("@")
        for item in splited_receive_item[:-1]:
            item_details = item.split('|')

            p = SaleProduct()
            p.salesID_id = obj.pk
            p.productID_id = item_details[0]
            p.productName = item_details[1]
            p.quantity = item_details[2]
            p.unitPrice = item_details[3]
            p.totalPrice = item_details[4]
            p.totalAmountAfterTax = item_details[4]
            p.remark = item_details[5]
            p.unit= item_details[6]
            p.ownerID_id = owner_id
            p.save()

        logger.info("Sales created successfully")
        return SuccessResponse("Sales created successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while creating Sales: {e}")
        return ErrorResponse("Unable to add new Sales. Please try again").to_json_response()


class SalesListJson(BaseDatatableView):
    order_columns = [ 'invoiceNumber','saleDate','customerID', 'totalAmount','totalTax', 'additionalCharge', 'totalAmountAfterTax', 'addedByID','dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        owner_id = get_owner_id(self.request)
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            staffID = self.request.GET.get("staffID")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')
            if staffID == 'All':
                return Sales.objects.select_related().filter(isDeleted__exact=False, ownerID_id=owner_id,saleDate__range=[sDate.date(), eDate.date()])
            else:
                return Sales.objects.select_related().filter(isDeleted__exact=False, ownerID_id=owner_id, saleDate__range=[sDate.date(), eDate.date()],
                                                             addedBy_id=int(staffID))


        except:
            return Sales.objects.select_related().filter(isDeleted__exact=False, ownerID_id=owner_id, saleDate__icontains=datetime.today().date())

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(invoiceNumber__icontains=search)
                |Q(saleDate__icontains=search)
                |Q(customerID__name__icontains=search)
                |Q(customerID__locationID__name__icontains=search)
                |Q(totalAmount__icontains=search)
                |Q(totalTax__icontains=search)
                |Q(additionalCharge__icontains=search)
                |Q(totalAmountAfterTax__icontains=search)
                |Q(addedByID__name__icontains=search)
                | Q(dateCreated__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            if 'Owner' or 'Manager' in self.request.user.groups.values_list('name', flat=True):
                action = '''<a href="/edit_sale/{}/" data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </a>
                  <button data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            else:
                action = '''<div class="ui tiny label">
                  Denied
                </div>'''


            json_data.append([
                escape(item.invoiceNumber),
                escape(item.saleDate.strftime('%d-%m-%Y')),
                escape(item.customerID.name) + ' - ' + escape(item.customerID.locationID.name),
                escape(item.totalAmount),
                escape(item.totalTax),
                escape(item.additionalCharge),
                escape(item.totalAmountAfterTax),
                escape(item.addedByID.name if item.addedByID else ''),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

                ])
        return json_data


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_sales_api(request):
    owner_id = get_owner_id(request)
    obj_id = request.POST.get("id")
    try:
        try:
            obj = Sales.objects.get(id=obj_id, isDeleted=False, ownerID_id=owner_id)
        except Sales.DoesNotExist:
            logger.error(f"Sales not found")
            return ErrorResponse("Sales not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()
        logger.info("Sales deleted successfully")
        return SuccessResponse("Sales deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting Sales: {e}")
        return ErrorResponse("Error while deleting Sales", status_code=500).to_json_response()



@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['customer', 'saleDate', 'grandTotal', 'additionalCharge', 'tax', 'datas', 'subTotal', 'id'])
@transaction.atomic
def update_sales_api(request):
    data = request.POST.dict()

    try:
        owner_id = get_owner_id(request)
        obj = Sales.objects.get(pk=data['id'], ownerID_id=owner_id, isDeleted=False)
        obj.customerID_id = data['customer']
        obj.saleDate = datetime.strptime(data['saleDate'], '%d/%m/%Y')
        obj.totalAmount = data['subTotal']
        obj.totalTax = data['tax']
        obj.additionalCharge = data['additionalCharge']
        obj.totalAmountAfterTax = data['grandTotal']
        obj.save()
        obj.invoiceNumber = "S"+str(Sales.objects.filter(ownerID_id=owner_id).count()).zfill(8)
        obj.save()
        splited_receive_item = data['datas'].split("@")
        old_items = SaleProduct.objects.filter(salesID_id=data['id'])
        for o in old_items:
            o.isDeleted = True
            o.save()

        for item in splited_receive_item[:-1]:
            item_details = item.split('|')

            p = SaleProduct()
            p.salesID_id = obj.pk
            p.productID_id = item_details[0]
            p.productName = item_details[1]
            p.quantity = item_details[2]
            p.unitPrice = item_details[3]
            p.totalPrice = item_details[4]
            p.totalAmountAfterTax = item_details[4]
            p.remark = item_details[5]
            p.unit= item_details[6]
            p.ownerID_id = owner_id
            p.save()

        logger.info("Sales updated successfully")
        return SuccessResponse("Sales updated successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while updated Sales: {e}")
        return ErrorResponse("Unable to update Sales. Please try again").to_json_response()



# ---------------------------- Manage Expense api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['expense_type', 'amount', 'description' ])
@transaction.atomic
def add_expense_api(request):
    data = request.POST.dict()
    try:
        obj = Expense(
            groupID_id=data['expense_type'],
            expenseAmount=data['amount'],
            expenseDescription=data['description'],
            expenseDate = datetime.today().date(),
            ownerID_id=get_owner_id(request),
        )
        obj.save()
        logger.info("Expense added successfully")
        return SuccessResponse("Expense added successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while adding expense: {e}")
        return ErrorResponse("Unable to add new expense. Please try again").to_json_response()


class ExpenseListJson(BaseDatatableView):
    order_columns = [ 'groupID','expenseAmount' ,'expenseDescription' , 'expenseDate' , 'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Expense.objects.select_related().filter(isDeleted__exact=False, ownerID_id=get_owner_id(self.request))

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(groupID__name__icontains=search)
                |Q(expenseAmount__icontains=search)
                |Q(expenseDescription__icontains=search) |Q(expenseDate__icontains=search)
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
                escape(item.groupID.name),
                escape(item.expenseAmount),
                escape(item.expenseDescription),
                escape(item.expenseDate.strftime('%d-%m-%Y %I:%M %p')),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_expense_api(request):

    obj_id = request.POST.get("id")
    try:
        try:
            obj = Expense.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
        except Expense.DoesNotExist:
            logger.error(f"Expense not found")
            return ErrorResponse("Expense not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()

        logger.info("Expense deleted successfully")
        return SuccessResponse("Expense deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting Expense : {e}")
        return ErrorResponse(str(e), status_code=500).to_json_response()



@require_http_methods(["GET"])
@validate_input(['id'])
def get_expense_detail(request):
    try:
        obj_id = request.GET.get('id')
        # Get single staff user
        try:
            obj = Expense.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
            data = {
                'id': obj.id,
                'groupID': obj.groupID.id,
                'expenseAmount': obj.expenseAmount,
                'expenseDescription': obj.expenseDescription,
                'expenseDate': obj.expenseDate,

            }
            logger.info("Expense fetched successfully")
            return SuccessResponse("Expense Group fetched successfully", data=data).to_json_response()
        except Expense.DoesNotExist:
            logger.error(f"Expense with ID '{obj_id}' not found")
            return ErrorResponse("Expense not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching Expense Group: {e}")
        return ErrorResponse( 'Unable to fetch expense group. Please try again', status_code=500).to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['id','expense_type', 'amount', 'description'  ])
@transaction.atomic
def update_expense_api(request):
    data = request.POST.dict()
    try:
        try:
            obj = Expense.objects.get(
                id=data['id'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
            )
        except Expense.DoesNotExist:
            logger.error(f"Expense  with ID {data["id"]}' not found")
            return ErrorResponse("Expense not found", status_code=404).to_json_response()

        obj.groupID_id = data['expense_type']
        obj.expenseAmount = data['amount']
        obj.expenseDescription = data['description']
        obj.save()

        logger.info(f"Expense '{data['id']}' updated successfully")
        return SuccessResponse("Expense updated successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while updating expense: {str(e)}")
        return ErrorResponse("Unable to update expense. Please try again", status_code=500).to_json_response()


# ---------------------------- Manage Expense api ---------------------------
@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['customer', 'jar_in','jar_out', 'remark' ])
@transaction.atomic
def add_jar_api(request):
    data = request.POST.dict()
    try:
        obj = JarCounter(
            customerID_id=data['customer'],
            inJar=data['jar_in'],
            outJar=data['jar_out'],
            remark=data['remark'],
            date = datetime.today().date(),
            ownerID_id=get_owner_id(request),
        )
        obj.save()
        logger.info("Jar record added successfully")
        return SuccessResponse("Jar record added successfully").to_json_response()
    except Exception as e:
        logger.error(f"Error while adding Jar record: {e}")
        return ErrorResponse("Unable to add new Jar record. Please try again").to_json_response()


class JarListJson(BaseDatatableView):
    order_columns = [ 'customerID','inJar' ,'outJar' ,'remark' , 'date' , 'dateCreated']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        owner_id = get_owner_id(self.request)
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            staffID = self.request.GET.get("staffID")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')
            if staffID == 'All':
                return JarCounter.objects.select_related().filter(isDeleted__exact=False, ownerID_id=owner_id,date__range=[sDate.date(), eDate.date()])
            else:
                return JarCounter.objects.select_related().filter(isDeleted__exact=False, ownerID_id=owner_id, date__range=[sDate.date(), eDate.date()],
                                                             addedBy_id=int(staffID))


        except:
            return JarCounter.objects.select_related().filter(isDeleted__exact=False, ownerID_id=owner_id, date__icontains=datetime.today().date())

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(customerID__name__icontains=search)
                |Q(inJar__icontains=search)    |Q(outJar__icontains=search)
                |Q(date__icontains=search)
                |Q(remark__icontains=search) |Q(customerID__locationID__name__icontains=search)
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
                escape(item.customerID.name) + ' - ' + escape(item.customerID.locationID.name),
                escape(int(item.inJar)),
                escape( int(item.outJar)),
                escape(item.remark),
                escape(item.date.strftime('%d-%m-%Y')),
                escape(item.dateCreated.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@csrf_exempt
@require_http_methods(["POST"])
@validate_input(["id"])
@transaction.atomic
def delete_jar_api(request):

    obj_id = request.POST.get("id")
    try:
        try:
            obj = JarCounter.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
        except JarCounter.DoesNotExist:
            logger.error(f"Jar entry not found")
            return ErrorResponse("Jar entry not found", status_code=404).to_json_response()

        # Soft delete
        obj.isDeleted = True
        obj.save()

        logger.info("Jar entry deleted successfully")
        return SuccessResponse("Jar entry deleted successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while deleting Jar entry : {e}")
        return ErrorResponse(str(e), status_code=500).to_json_response()



@require_http_methods(["GET"])
@validate_input(['id'])
def get_jar_detail(request):
    try:
        obj_id = request.GET.get('id')
        # Get single staff user
        try:
            obj = JarCounter.objects.get(id=obj_id, isDeleted=False, ownerID_id=get_owner_id(request))
            data = {
                'id': obj.id,
                'customerID': obj.customerID_id,
                'inJar': obj.inJar,
                'outJar': obj.outJar,
                'remark': obj.remark,
                'date': obj.date,

            }
            logger.info("Jar entry fetched successfully")
            return SuccessResponse("Jar entry fetched successfully", data=data).to_json_response()
        except JarCounter.DoesNotExist:
            logger.error(f"Jar entry with ID '{obj_id}' not found")
            return ErrorResponse("Jar entry not found", status_code=404).to_json_response()

    except Exception as e:
        logger.error(f"Error while fetching Jar entry: {e}")
        return ErrorResponse( 'Unable to fetch Jar entry. Please try again', status_code=500).to_json_response()

@csrf_exempt
@require_http_methods(['POST'])
@validate_input(['id','customer', 'jar_in','jar_out', 'remark' ])
@transaction.atomic
def update_jar_api(request):
    data = request.POST.dict()
    try:
        try:
            obj = JarCounter.objects.get(
                id=data['id'],
                ownerID_id=get_owner_id(request),
                isDeleted=False
            )
        except JarCounter.DoesNotExist:
            logger.error(f"Expense  with ID {data["id"]}' not found")
            return ErrorResponse("Expense not found", status_code=404).to_json_response()

        obj.customerID_id = data['customer']
        obj.inJar = data['jar_in']
        obj.outJar = data['jar_out']
        obj.remark = data['remark']
        obj.save()

        logger.info(f"Jar entry '{data['id']}' updated successfully")
        return SuccessResponse("Jar entry updated successfully").to_json_response()

    except Exception as e:
        logger.error(f"Error while updating Jar entry: {str(e)}")
        return ErrorResponse("Unable to update Jar entry. Please try again", status_code=500).to_json_response()
