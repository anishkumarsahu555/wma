
from wmaApp.models import Owner, StaffUser

def get_owner_id(request):
    """Get the owner ID from either StaffUser or Owner model for the current user."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None

    # First check if user is StaffUser
    staff = StaffUser.objects.filter(userID=user).select_related("ownerID").first()
    if staff and staff.ownerID:
        return staff.ownerID_id  # Direct FK id

    # Otherwise, check if user is Owner
    owner = Owner.objects.filter(userID=user).first()
    if owner:
        return owner.id

    return None

def get_user_id(request):
    """Get the user ID from staff"""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None

    # First check if user is StaffUser
    staff = StaffUser.objects.filter(userID=user.pk).first()
    if staff:
        return staff.pk  # Direct FK id
    return None