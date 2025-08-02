import logging 
from commons.utils.MongoDBClient import MongoDBClient

logger = logging.getLogger(__name__)

class VendorService:
    @staticmethod
    def register_vendor(vendor_data: dict) -> bool:
        vendors = MongoDBClient.get_collection("vendors")
        existing = vendors.find_one({"vendor_id": vendor_data["vendor_id"]})
        if existing:
            logger.warning(f"Vendor with ID {vendor_data['vendor_id']} already exists.")
            return False
        vendors.insert_one(vendor_data)
        logger.info(f"Vendor with ID {vendor_data['vendor_id']} added successfully.")
        return True 

    @staticmethod
    def get_vendor(vendor_id: str) -> dict:
        vendors = MongoDBClient().get_collection("vendors")
        return vendors.find_one({"vendor_id": vendor_id})