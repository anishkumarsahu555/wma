from django.contrib.auth.models import User
from django.db import models
from stdimage import StdImageField

class Owner(models.Model):
    userID = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True)
    profile_pic = StdImageField(upload_to='owner_pics', variations={'thumb': (128, 128)}, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    startDate = models.DateField(blank=True, null=True)
    isActive = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
            return self.name

class UserGroup(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

class StaffUser(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    groupID = models.ForeignKey(UserGroup, on_delete=models.CASCADE,null=True, blank=True)
    userID = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True)
    profile_pic = StdImageField(upload_to='staff_pics', variations={'thumb': (128, 128)}, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    startDate = models.DateField(blank=True, null=True)
    isActive = models.BooleanField(default=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

class ExpenseGroup(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    staffID = models.ForeignKey(StaffUser, on_delete=models.CASCADE,null=True, blank=True)
    groupID = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE,null=True, blank=True)
    expenseDate = models.DateField(blank=True, null=True)
    expenseAmount = models.FloatField(default=0.00)
    expenseDescription = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.expenseDescription

class Location(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

class Customer(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    locationID = models.ForeignKey(Location, on_delete=models.CASCADE,null=True, blank=True)
    profile_pic = StdImageField(upload_to='customer_pics', variations={'thumb': (128, 128)}, null=True, blank=True)
    customerId = models.CharField(max_length=100, blank=True, null=True)
    userID = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    addedByID = models.ForeignKey(StaffUser, on_delete=models.CASCADE, null=True, blank=True)
    isActive = models.BooleanField(default=True)
    addedDate = models.DateField(blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

class CustomerLedger(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    customerID = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True, blank=True)
    debit = models.FloatField(default=0.00)
    credit = models.FloatField(default=0.00)
    balanceAtDate = models.FloatField(default=0.00)
    balance = models.FloatField(default=0.00)
    isDeleted = models.BooleanField(default=False)
    addedByID = models.ForeignKey(StaffUser, on_delete=models.CASCADE, null=True, blank=True)
    addedDate = models.DateField(blank=True, null=True)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.customerID.name

class TaxAndHsn(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    taxRate = models.FloatField(default=0.00)
    hsn = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    def __str__(self):
        return self.hsn

class Category(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

class Unit(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    productName = models.CharField(max_length=100, blank=True, null=True)
    productDescription = models.CharField(max_length=100, blank=True, null=True)
    rate = models.FloatField(default=0.00)
    quantity = models.FloatField(default=0)
    sp = models.FloatField(default=0.00)
    unitID = models.ForeignKey(Unit, on_delete=models.CASCADE,null=True, blank=True)
    categoryID = models.ForeignKey(Category, on_delete=models.CASCADE,null=True, blank=True)
    taxID = models.ForeignKey(TaxAndHsn, on_delete=models.CASCADE,null=True, blank=True)
    isDeleted = models.BooleanField(default=False)
    draft = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.productName

class ProductImage(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    productID = models.ForeignKey(Product, on_delete=models.CASCADE,null=True, blank=True)
    image = StdImageField(upload_to='product_pics', variations={'thumb': (128, 128)}, null=True, blank=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    def __str__(self):
        return self.productID.name


class Supplier(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    gstin = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name

class Purchase(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    customerID = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True, blank=True)
    supplierID = models.ForeignKey(Supplier, on_delete=models.CASCADE,null=True, blank=True)
    invoiceNumber = models.CharField(max_length=100, blank=True, null=True)
    invoiceDate = models.DateField(blank=True, null=True)
    totalAmount = models.FloatField(default=0.00)
    totalTax = models.FloatField(default=0.00)
    additionalCharge = models.FloatField(default=0.00)
    totalAmountAfterAdditionalCharge = models.FloatField(default=0.00)
    remark = models.TextField( blank=True, null=True)
    addedByID = models.ForeignKey(StaffUser, on_delete=models.CASCADE, null=True, blank=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.customerID.name

class PurchaseProduct(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    productID = models.ForeignKey(Product, on_delete=models.CASCADE,null=True, blank=True)
    purchaseID = models.ForeignKey(Purchase, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.FloatField(default=0.00)
    unitPrice = models.FloatField(default=0.00)
    totalPrice = models.FloatField(default=0.00)
    taxRate = models.FloatField(default=0.00)
    taxAmount = models.FloatField(default=0.00)
    totalAmountAfterTax = models.FloatField(default=0.00)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return

class Sales(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    customerID = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True, blank=True)
    invoiceNumber = models.CharField(max_length=100, blank=True, null=True)
    saleDate = models.DateField(blank=True, null=True)
    totalAmount = models.FloatField(default=0.00)
    totalTax = models.FloatField(default=0.00)
    additionalCharge = models.FloatField(default=0.00)
    totalAmountAfterTax = models.FloatField(default=0.00)
    remark = models.TextField( blank=True, null=True)
    addedByID = models.ForeignKey(StaffUser, on_delete=models.CASCADE, null=True, blank=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.customerID.name

class SaleProduct(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    productID = models.ForeignKey(Product, on_delete=models.CASCADE,null=True, blank=True)
    salesID = models.ForeignKey(Sales, on_delete=models.CASCADE, null=True, blank=True)
    productName = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=100, blank=True, null=True)
    remark = models.TextField( blank=True, null=True)
    quantity = models.FloatField(default=0.00)
    unitPrice = models.FloatField(default=0.00)
    totalPrice = models.FloatField(default=0.00)
    taxRate = models.FloatField(default=0.00)
    taxAmount = models.FloatField(default=0.00)
    totalAmountAfterTax = models.FloatField(default=0.00)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.productID.productName


class Payment(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    customerID = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True, blank=True)
    paymentDate = models.DateField(blank=True, null=True)
    paymentAmount = models.FloatField(default=0.00)
    remark = models.TextField( blank=True, null=True)
    addedByID = models.ForeignKey(StaffUser, on_delete=models.CASCADE, null=True, blank=True)
    isDeleted = models.BooleanField(default=False)
    isApprove = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.customerID.name

class AdvanceOrder(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    customerID = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True, blank=True)
    invoiceNumber = models.CharField(max_length=100, blank=True, null=True)
    orderDate = models.DateField(blank=True, null=True)
    expectedDeliveryDate = models.DateField(blank=True, null=True)
    totalAmount = models.FloatField(default=0.00)
    totalTax = models.FloatField(default=0.00)
    additionalCharge = models.FloatField(default=0.00)
    totalAmountAfterTax = models.FloatField(default=0.00)
    remark = models.TextField( blank=True, null=True)
    addedByID = models.ForeignKey(StaffUser, on_delete=models.CASCADE, null=True, blank=True)
    isDeleted = models.BooleanField(default=False)
    isDelivered = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.customerID.name

class AdvanceOrderProduct(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    productID = models.ForeignKey(Product, on_delete=models.CASCADE,null=True, blank=True)
    orderID = models.ForeignKey(AdvanceOrder, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.FloatField(default=0.00)
    unitPrice = models.FloatField(default=0.00)
    totalPrice = models.FloatField(default=0.00)
    taxRate = models.FloatField(default=0.00)
    taxAmount = models.FloatField(default=0.00)
    totalAmountAfterTax = models.FloatField(default=0.00)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.productID.name

class JarCounter(models.Model):
    ownerID = models.ForeignKey(Owner, on_delete=models.CASCADE,null=True, blank=True)
    customerID = models.ForeignKey(Customer, on_delete=models.CASCADE,null=True, blank=True)
    inJar = models.FloatField(default=0.00)
    outJar = models.FloatField(default=0.00)
    date = models.DateField(blank=True, null=True)
    addedByID = models.ForeignKey(StaffUser, on_delete=models.CASCADE, null=True, blank=True)
    isDeleted = models.BooleanField(default=False)
    dateCreated = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.customerID.name