from django.core.exceptions import ObjectDoesNotExist

from wmaApp.models import Owner, StaffUser


def get_owner_id(request):
    """Get the owner ID from either StaffUser or Owner model for the current user."""
    try:
        user_id = request.user.pk
        try:
            return StaffUser.objects.get(userID_id=user_id).ownerID.id
        except ObjectDoesNotExist:
            return Owner.objects.get(userID_id=user_id).id
    except (ObjectDoesNotExist, AttributeError):
        return None
