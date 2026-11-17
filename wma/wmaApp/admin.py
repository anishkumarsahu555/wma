from django.contrib import admin
from django.utils.html import format_html
from .models import *

admin.site.site_header = "Water Management Admin"
admin.site.site_title = "WMA Admin"
admin.site.index_title = "Operations Dashboard"


class BaseAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_max_show_all = 200
    save_on_top = True
    preserve_filters = True
    actions_on_top = True
    actions_on_bottom = True


class ImagePreviewMixin:
    def image_preview(self, obj):
        if hasattr(obj, "profile_pic") and obj.profile_pic:
            return format_html(
                '<img src="{}" width="44" height="44" style="border-radius:50%; object-fit:cover;" />',
                obj.profile_pic.url,
            )
        if hasattr(obj, "image") and obj.image:
            return format_html(
                '<img src="{}" width="44" height="44" style="object-fit:cover;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Preview"


class ActiveDeletedMixin:
    actions = ["mark_active", "mark_inactive", "mark_deleted", "restore_selected"]

    @admin.action(description="Mark selected as active")
    def mark_active(self, request, queryset):
        if hasattr(self.model, "isActive"):
            queryset.update(isActive=True)

    @admin.action(description="Mark selected as inactive")
    def mark_inactive(self, request, queryset):
        if hasattr(self.model, "isActive"):
            queryset.update(isActive=False)

    @admin.action(description="Soft delete selected")
    def mark_deleted(self, request, queryset):
        if hasattr(self.model, "isDeleted"):
            queryset.update(isDeleted=True)

    @admin.action(description="Restore selected")
    def restore_selected(self, request, queryset):
        if hasattr(self.model, "isDeleted"):
            queryset.update(isDeleted=False)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    show_change_link = True


class SaleProductInline(admin.TabularInline):
    model = SaleProduct
    extra = 0
    show_change_link = True


class PurchaseProductInline(admin.TabularInline):
    model = PurchaseProduct
    extra = 0
    show_change_link = True


@admin.register(Owner)
class OwnerAdmin(ImagePreviewMixin, ActiveDeletedMixin, BaseAdmin):
    list_display = (
        "image_preview",
        "name",
        "username",
        "email",
        "phone",
        "isActive",
        "isDeleted",
        "dateCreated",
    )
    search_fields = ("name", "username", "email", "phone")
    list_filter = ("isActive", "isDeleted", "startDate")
    ordering = ("-dateCreated",)
    readonly_fields = ("dateCreated", "lastUpdatedOn", "image_preview")
    raw_id_fields = ("userID",)
    fieldsets = (
        (
            "Basic Info",
            {
                "fields": (
                    "image_preview",
                    "profile_pic",
                    "name",
                    "username",
                    "password",
                    "email",
                    "phone",
                    "address",
                    "userID",
                )
            },
        ),
        ("Status", {"fields": ("isActive", "isDeleted", "startDate")}),
        (
            "Timestamps",
            {"fields": ("dateCreated", "lastUpdatedOn"), "classes": ("collapse",)},
        ),
    )


@admin.register(UserGroup)
class UserGroupAdmin(ActiveDeletedMixin, BaseAdmin):
    list_display = ("name", "ownerID", "isDeleted", "dateCreated")
    search_fields = ("name", "ownerID__name")
    list_filter = ("isDeleted", "ownerID")
    ordering = ("-dateCreated",)
    list_select_related = ("ownerID",)


@admin.register(StaffUser)
class StaffUserAdmin(ImagePreviewMixin, ActiveDeletedMixin, BaseAdmin):
    list_display = (
        "image_preview",
        "name",
        "username",
        "email",
        "phone",
        "groupID",
        "locationID",
        "isActive",
        "isDeleted",
        "dateCreated",
    )
    search_fields = ("name", "username", "email", "phone", "groupID__name")
    list_filter = ("isActive", "isDeleted", "groupID", "locationID")
    ordering = ("-dateCreated",)
    list_select_related = ("groupID", "locationID", "ownerID")
    readonly_fields = ("image_preview", "dateCreated", "lastUpdatedOn")
    raw_id_fields = ("userID",)


@admin.register(Product)
class ProductAdmin(ActiveDeletedMixin, BaseAdmin):
    list_display = (
        "productName",
        "rate",
        "quantity",
        "sp",
        "unitID",
        "categoryID",
        "taxID",
        "isDeleted",
    )
    search_fields = ("productName", "productDescription")
    list_filter = ("categoryID", "unitID", "taxID", "isDeleted")
    ordering = ("-dateCreated",)
    list_select_related = ("unitID", "categoryID", "taxID", "ownerID")
    inlines = [ProductImageInline]


@admin.register(Sales)
class SalesAdmin(BaseAdmin):
    list_display = (
        "invoiceNumber",
        "customerID",
        "saleDate",
        "totalAmount",
        "totalTax",
        "additionalCharge",
        "totalAmountAfterTax",
        "isDeleted",
    )
    search_fields = ("invoiceNumber", "customerID__name")
    list_filter = ("saleDate", "isDeleted", "ownerID", "addedByID")
    date_hierarchy = "saleDate"
    ordering = ("-saleDate", "-id")
    list_select_related = ("customerID", "addedByID", "ownerID")
    inlines = [SaleProductInline]


@admin.register(Purchase)
class PurchaseAdmin(BaseAdmin):
    list_display = (
        "invoiceNumber",
        "supplierID",
        "invoiceDate",
        "totalAmount",
        "totalTax",
        "additionalCharge",
        "totalAmountAfterAdditionalCharge",
        "isDeleted",
    )
    search_fields = ("invoiceNumber", "supplierID__name")
    list_filter = ("invoiceDate", "isDeleted", "ownerID")
    date_hierarchy = "invoiceDate"
    ordering = ("-invoiceDate", "-id")
    list_select_related = ("supplierID", "ownerID")
    inlines = [PurchaseProductInline]


@admin.register(Customer)
class CustomerAdmin(ImagePreviewMixin, ActiveDeletedMixin, BaseAdmin):
    list_display = (
        "image_preview",
        "customerId",
        "name",
        "phone",
        "email",
        "locationID",
        "addedByID",
        "isActive",
        "isDeleted",
    )
    search_fields = ("customerId", "name", "phone", "email", "address")
    list_filter = ("isActive", "isDeleted", "locationID", "ownerID")
    ordering = ("-dateCreated",)
    list_select_related = ("locationID", "addedByID", "ownerID")
    readonly_fields = ("image_preview", "dateCreated", "lastUpdatedOn")
    raw_id_fields = ("userID",)


@admin.register(Expense)
class ExpenseAdmin(BaseAdmin):
    list_display = (
        "groupID",
        "expenseAmount",
        "expenseDate",
        "staffID",
        "ownerID",
        "isDeleted",
    )
    search_fields = ("groupID__name", "expenseDescription", "staffID__name")
    list_filter = ("isDeleted", "expenseDate", "groupID", "ownerID", "staffID")
    date_hierarchy = "expenseDate"
    ordering = ("-expenseDate", "-id")
    list_select_related = ("groupID", "staffID", "ownerID")


@admin.register(Payment)
class PaymentAdmin(BaseAdmin):
    list_display = (
        "customerID",
        "paymentAmount",
        "paymentDate",
        "addedByID",
        "approvedBy",
        "isApprove",
        "isDeleted",
    )
    search_fields = ("customerID__name", "remark")
    list_filter = ("paymentDate", "isApprove", "isDeleted", "ownerID", "addedByID")
    date_hierarchy = "paymentDate"
    ordering = ("-paymentDate", "-id")
    list_select_related = ("customerID", "addedByID", "approvedBy", "ownerID")


@admin.register(AdvanceOrder)
class AdvanceOrderAdmin(BaseAdmin):
    list_display = (
        "invoiceNumber",
        "customerID",
        "orderDate",
        "expectedDeliveryDate",
        "totalAmountAfterTax",
        "isDelivered",
        "isDeleted",
    )
    search_fields = ("invoiceNumber", "customerID__name")
    list_filter = ("isDelivered", "isDeleted", "orderDate", "expectedDeliveryDate", "ownerID")
    date_hierarchy = "expectedDeliveryDate"
    ordering = ("-expectedDeliveryDate", "-id")
    list_select_related = ("customerID", "addedByID", "ownerID")


@admin.register(JarCounter)
class JarCounterAdmin(BaseAdmin):
    list_display = ("customerID", "inJar", "outJar", "date", "addedByID", "isDeleted")
    search_fields = ("customerID__name", "remark", "addedByID__name")
    list_filter = ("isDeleted", "date", "ownerID", "addedByID")
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    list_select_related = ("customerID", "addedByID", "ownerID")


@admin.register(JarAllocation)
class JarAllocationAdmin(BaseAdmin):
    list_display = ("driverID", "inJar", "outJar", "date", "addedByID", "isDeleted")
    search_fields = ("driverID__name", "remark", "addedByID__name")
    list_filter = ("isDeleted", "date", "ownerID", "driverID", "addedByID")
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    list_select_related = ("driverID", "addedByID", "ownerID")


@admin.register(Location)
class LocationAdmin(BaseAdmin):
    list_display = ("name", "ownerID", "isDeleted", "dateCreated")
    search_fields = ("name", "ownerID__name")
    list_filter = ("isDeleted", "ownerID")
    ordering = ("name",)
    list_select_related = ("ownerID",)


@admin.register(ExpenseGroup)
class ExpenseGroupAdmin(BaseAdmin):
    list_display = ("name", "ownerID", "isDeleted", "dateCreated")
    search_fields = ("name", "ownerID__name")
    list_filter = ("isDeleted", "ownerID")
    ordering = ("name",)
    list_select_related = ("ownerID",)


@admin.register(TaxAndHsn)
class TaxAndHsnAdmin(BaseAdmin):
    list_display = ("hsn", "taxRate", "ownerID", "isDeleted", "dateCreated")
    search_fields = ("hsn",)
    list_filter = ("isDeleted", "ownerID")
    ordering = ("hsn",)
    list_select_related = ("ownerID",)


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ("name", "ownerID", "isDeleted", "dateCreated")
    search_fields = ("name", "ownerID__name")
    list_filter = ("isDeleted", "ownerID")
    ordering = ("name",)
    list_select_related = ("ownerID",)


@admin.register(Unit)
class UnitAdmin(BaseAdmin):
    list_display = ("name", "ownerID", "isDeleted", "dateCreated")
    search_fields = ("name", "ownerID__name")
    list_filter = ("isDeleted", "ownerID")
    ordering = ("name",)
    list_select_related = ("ownerID",)


@admin.register(Supplier)
class SupplierAdmin(BaseAdmin):
    list_display = ("name", "phone", "email", "ownerID", "isDeleted")
    search_fields = ("name", "phone", "email", "gstin")
    list_filter = ("isDeleted", "ownerID")
    ordering = ("name",)
    list_select_related = ("ownerID",)


@admin.register(CustomerLedger)
class CustomerLedgerAdmin(BaseAdmin):
    list_display = (
        "customerID",
        "addedDate",
        "credit",
        "debit",
        "balance",
        "addedByID",
        "isDeleted",
    )
    search_fields = ("customerID__name", "remark")
    list_filter = ("isDeleted", "addedDate", "ownerID", "addedByID")
    date_hierarchy = "addedDate"
    ordering = ("-addedDate", "-id")
    list_select_related = ("customerID", "addedByID", "ownerID")


models_to_register = [SaleProduct, AdvanceOrderProduct]
for model in models_to_register:
    admin.site.register(model)
