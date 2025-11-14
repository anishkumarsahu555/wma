from datetime import datetime

from utils.get_user_id_detail import get_user_id, get_owner_id
from utils.logger import logger
from wmaApp.models import CustomerLedger

def generate_customer_ledger(request,customer_id, payment_type, amount, remark):
    try:
        ledger = CustomerLedger()
        ledger.remark = remark
        ledger.addedDate = datetime.now().date()
        ledger.customerID_id = customer_id
        try:
            last_customer_ledger = CustomerLedger.objects.filter(customerID_id= customer_id).last()
            bal = last_customer_ledger.balance
        except:
            bal = 0
        # Convert amount to float to ensure numeric operations
        amount = float(amount)
        
        if payment_type == 'credit':
            ledger.credit = amount
            ledger.balance = bal + amount
            ledger.isCredit = True

        if payment_type == 'debit':
            ledger.debit = amount
            ledger.balance = bal - amount
        ledger.balanceAtDate = bal
        ledger.ownerID_id = get_owner_id(request)
        ledger.addedByID_id = get_user_id(request)
        ledger.save()
        logger.info("Customer Ledger Balance {}: {}".format(ledger.customerID.name, ledger.balance))
        return ledger
    except Exception as e:
        logger.error(f"Error in generate_customer_ledger {e}")
        return None


