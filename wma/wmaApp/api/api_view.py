from datetime import datetime
from django.db import transaction
from django.db.models import Q
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

#
# def add_customer_api():
#     if request.method == 'POST':
#         try:
#             CompanyUserName = request.POST.get("CompanyUserName")
#             UserPhoneNo = request.POST.get("UserPhoneNo")
#             UserEmail = request.POST.get("UserEmail")
#             UserAddress = request.POST.get("UserAddress")
#             UserGroup = request.POST.get("UserGroup")
#             UserStatus = request.POST.get("UserStatus")
#             UserPwd = request.POST.get("UserPwd")
#             # PartyGroup = request.POST.get("PartyGroup")
#             imageUpload = request.FILES["imageUpload"]
#             imageUploadID = request.FILES["imageUploadID"]
#
#             staff = StaffUser()
#             staff.photo = imageUpload
#             staff.idProof = imageUploadID
#             staff.name = CompanyUserName
#             staff.phone = UserPhoneNo
#             staff.email = UserEmail
#             staff.address = UserAddress
#             staff.group = UserGroup
#             staff.isActive = UserStatus
#             staff.userPassword = UserPwd
#             # try:
#             #     staff.partyGroupID_id = int(PartyGroup)
#             # except:
#             #     pass
#             staff.save()
#             username = 'USER' + get_random_string(length=3, allowed_chars='1234567890')
#             while User.objects.select_related().filter(username__exact=username).count() > 0:
#                 username = 'USER' + get_random_string(length=5, allowed_chars='1234567890')
#             else:
#                 new_user = User()
#                 new_user.username = username
#                 new_user.set_password(UserPwd)
#
#                 new_user.save()
#                 staff.username = username
#                 staff.user_ID_id = new_user.pk
#
#                 staff.save()
#
#                 try:
#                     g = Group.objects.get(name=UserGroup)
#                     g.user_set.add(new_user.pk)
#                     g.save()
#
#                 except:
#                     g = Group()
#                     g.name = UserGroup
#                     g.save()
#                     g.user_set.add(new_user.pk)
#                     g.save()
#             return JsonResponse({'message': 'success'}, safe=False)
#         except:
#             return JsonResponse({'message': 'error'}, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
@validate_input(['name'])
def add_customer_api(request):
    logger.info("add_customer_api")
    return SuccessResponse("success").to_json_response()
