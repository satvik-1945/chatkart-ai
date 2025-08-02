import logging 
from commons.utils.MongoDBClient import MongoDBClient

logger = logging.getLogger(__name__)

class InventoryService:
    @staticmethod
    def add_article(article_data:dict) -> bool:
        inventory = MongoDBClient().get_collection("inventory")
        existing = inventory.find_one({"article_id": article_data["article_id"]})
        if existing:
            logger.warning(f"Article with ID {article_data['article_id']} already exists.")
            return False
        inventory.insert_one(article_data)
        logger.info(f"Article with ID {article_data['article_id']} added successfully.")
        return True
    
    @staticmethod
    def get_vendor_inventory(vendor_id: str) -> list:
        inventory = MongoDBClient().get_collection("inventory")
        return list(inventory.find({"vendor_id": vendor_id}))
    
    @staticmethod
    def update_variant_qty(vendor_id: str, article_id: str, color: str, size: str, qty: int) -> bool:
        inventory = MongoDBClient.get_collection("inventory")
        result = inventory.update_one(
            {
                "vendor_id": vendor_id,
                "article_id": article_id,
                "variants": {"$elemMatch": {"color": color, "size": size}}
            },
            {"$set": {"variants.$.total_items": qty}}
        )
        if result.modified_count > 0:
            logger.info(f"✅ Updated {article_id} variant {color}/{size} → {qty}")
            return True
        logger.warning("No matching variant found to update.")
        return False