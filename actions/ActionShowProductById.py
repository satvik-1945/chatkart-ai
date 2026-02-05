
import re
from datetime import datetime
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from commons.utils.InventoryService import InventoryService

class ActionShowProductById(Action):
    def name(self) -> Text:
        return "action_show_product_by_id"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        vendor_id = tracker.get_slot("vendor_id")
        
        article_id = next(tracker.get_latest_entity_values("article_id"), None) or tracker.get_slot("article_id")

        if article_id:
            # --- HAPPY PATH: User provided the full ID ---
            product = InventoryService.get_article_by_id(vendor_id, article_id)
            if product:
                response_text = (
                    f"Found it! Here are the details for {article_id}:\n"
                    f"Name: {product.get('name', 'N/A')}\n"
                    f"Description: {product.get('description', 'N/A')}\n"
                    f"Price: ${product.get('price', 'N/A')}\n"
                    "Would you like to add this to your cart?"
                )
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(text=f"I'm sorry, I couldn't find article '{article_id}' for this vendor.")
        
        else:
            # --- CLARIFICATION PATH: User might have forgotten the date ---
            user_text = tracker.latest_message.get('text', '')
            # Look for just the item number part (e.g., "-25", "number 5")
            match = re.search(r'[-#]?\s?(\d{1,3})$', user_text)

            if match:
                item_number = match.group(1)
                # Set a slot to remember the number
                SlotSet("partial_item_number", item_number)
                # Ask the user for the missing date
                dispatcher.utter_message(text="I see you're looking for item number "
                                              f"{item_number}. Which date's live stream was that from? "
                                              "For example, you can say '21may25'.")
            else:
                dispatcher.utter_message(text="I'm sorry, I didn't understand the article number. "
                                              "Please use the format like '21may25-1'.")

        return []
