from django.contrib import admin
from django.utils.html import format_html
from .models import *

# ---------- Helper Mixins ----------
class ImagePreviewMixin:
    """Show image preview in list & detail pages"""
    def image_preview(self, obj):
        if hasattr(obj, 'profile_pic') and obj.profile_pic:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;" />', obj.profile_pic.url)
        elif hasattr(obj, 'image') and obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'


class ActiveDeletedMixin:
    """Custom admin actions for activating/deleting"""
    actions = ['mark_active', 'mark_inactive', 'mark_deleted']

    def mark_active(self, request, queryset):
        queryset.update(isActive=True)
    mark_active.short_description = "Mark selected as Active"

    def mark_inactive(self, request, queryset):
        queryset.update(isActive=False)
    mark_inactive.short_description = "Mark selected as Inactive"

    def mark_deleted(self, request, queryset):
        queryset.update(isDeleted=True)
    mark_deleted.short_description = "Mark selected as Deleted"


# ---------- Inline Models ----------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class SaleProductInline(admin.TabularInline):
    model = SaleProduct
    extra = 1


class PurchaseProductInline(admin.TabularInline):
    model = PurchaseProduct
    extra = 1


# ---------- Admin Registrations ----------
@admin.register(Owner)
class OwnerAdmin(ImagePreviewMixin, ActiveDeletedMixin, admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'username', 'email', 'phone', 'isActive', 'isDeleted', 'dateCreated')
    search_fields = ('name', 'username', 'email', 'phone')
    list_filter = ('isActive', 'isDeleted', 'startDate')
    readonly_fields = ('dateCreated', 'lastUpdatedOn', 'image_preview')
    fieldsets = (
        ("Basic Info", {'fields': ('image_preview', 'profile_pic', 'name', 'username', 'password', 'email', 'phone', 'address','userID')}),
        ("Status", {'fields': ('isActive', 'isDeleted', 'startDate')}),
        ("Timestamps", {'fields': ('dateCreated', 'lastUpdatedOn'), 'classes': ('collapse',)}),
    )


@admin.register(UserGroup)
class UserGroupAdmin(ActiveDeletedMixin, admin.ModelAdmin):
    list_display = ('name', 'ownerID', 'isDeleted', 'dateCreated')
    search_fields = ('name', 'ownerID__name')
    list_filter = ('isDeleted',)


@admin.register(StaffUser)
class StaffUserAdmin(ImagePreviewMixin, ActiveDeletedMixin, admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'username', 'email', 'phone', 'groupID', 'isActive', 'isDeleted', 'dateCreated', 'lastUpdatedOn')
    search_fields = ('name', 'username', 'email', 'phone')
    list_filter = ('isActive', 'isDeleted', 'groupID')
    readonly_fields = ('image_preview',)


@admin.register(Product)
class ProductAdmin(ActiveDeletedMixin, admin.ModelAdmin):
    list_display = ('productName', 'rate', 'quantity', 'unitID', 'categoryID', 'taxID', 'isDeleted')
    search_fields = ('productName', 'productDescription')
    list_filter = ('categoryID', 'unitID', 'taxID', 'isDeleted')
    inlines = [ProductImageInline]


@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = ('invoiceNumber', 'customerID', 'saleDate', 'totalAmount', 'totalAmountAfterTax')
    search_fields = ('invoiceNumber', 'customerID__name')
    list_filter = ('saleDate', 'isDeleted')
    date_hierarchy = 'saleDate'
    inlines = [SaleProductInline]


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoiceNumber', 'supplierID', 'invoiceDate', 'totalAmountAfterAdditionalCharge')
    search_fields = ('invoiceNumber', 'supplierID__name')
    list_filter = ('invoiceDate', 'isDeleted')
    date_hierarchy = 'invoiceDate'
    inlines = [PurchaseProductInline]


@admin.register(Customer)
class CustomerAdmin(ImagePreviewMixin, ActiveDeletedMixin, admin.ModelAdmin):
    list_display = ('image_preview', 'customerId', 'name', 'phone', 'email', 'locationID', 'isDeleted')
    search_fields = ('customerId', 'name', 'phone', 'email')
    list_filter = ('isDeleted', 'locationID')
    readonly_fields = ('image_preview',)


# ---------- Register remaining without customization ----------
models_to_register = [
    ExpenseGroup, Expense, Location, CustomerLedger, TaxAndHsn, Category, Unit,
    Supplier, SaleProduct, Payment, AdvanceOrder, AdvanceOrderProduct, JarCounter,
]

for model in models_to_register:
    admin.site.register(model)