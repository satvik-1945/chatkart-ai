import logging
from commons.utils.MongoDBClient import MongoDBClient

logger = logging.getLogger(__name__)

class CustomerService:
    @staticmethod
    def add_customer(customer_data: dict)-> bool:
        customers = MongoDBClient().get_collection("customers")
        existing = customers.find_one({"vendor_id":customer_data.get("vendor_id"),"phone_number": customer_data["phone_number"]})
        if existing:
            logger.warning(f"Customer with phone number {customer_data['phone_number']} already exists for vendor {customer_data['vendor_id']}. ")
            return False
        
        customers.insert_one(customer_data)
        logger.info(f"Customer with phone number {customer_data['phone_number']} added for vendor {customer_data['vendor_id']}. ")
        return True 
    
    @staticmethod
    def get_customer(vendor_id: str, phone_number: str) -> dict:
        customers = MongoDBClient().get_collection("customers")
        return customers.find_one({"phone_number": phone_number, "vendor_id": vendor_id})