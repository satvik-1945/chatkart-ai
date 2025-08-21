from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher  
from rasa_sdk.events import SlotSet, EventType, SessionStarted, ActionExecuted
from rasa_sdk.forms import FormValidationAction
from commons.utils.MongoDBClient import MongoDBClient
from commons.utils.CustomerService import CustomerService
from commons.utils.InventoryService import InventoryService
from commons.utils.VendorService import VendorService
import logging

logger = logging.getLogger(__name__)

USER_PROFILE = {}
ORDERS = {}

class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # This is where you would extract the vendor_id from the initial payload.
        # For example, if the user comes from a link like "wa.me/123?text=start_vendor_v123",
        # you would parse "v123" from the text.

        # FOR NOW, WE WILL HARDCODE IT FOR DEVELOPMENT AND TESTING.
        vendor_id = "vendor_123" # Replace with your logic later

        events = [SessionStarted()]

        events.append(SlotSet("vendor_id", vendor_id))

        # it tells Rasa to continue with the default behavior
        events.append(ActionExecuted("action_listen"))

        logger.info(f"Session started for vendor_id: {vendor_id}")

        return events


class ValidateProfileForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_profile_form"

    async def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        
        vendor_id = tracker.get_slot("vendor_id")
        if not vendor_id:
            logger.error(f"CRITICAL: vendor_id is not set for sender_id {tracker.sender_id}.")
            dispatcher.utter_message(text="Sorry, we've run into a system error. Please try again later.")
            return []

        customer_data = {
            "vendor_id": vendor_id,
            "name": tracker.get_slot("name"),
            "phone_number": tracker.get_slot("phone_number"),
            "address": tracker.get_slot("address"),
            "email": tracker.get_slot("email"),
        }

        success = CustomerService.add_customer(customer_data)

        if success:
            dispatcher.utter_message(
                response="utter_profile_created",
                name=customer_data['name']
            )
        else:
            dispatcher.utter_message(
                text=f"It looks like the phone number {customer_data['phone_number']} is already registered with us. ⚠️"
            )

        return []    

class ActionChangeAddress(Action):
    def name(self) -> Text:
        return "action_change_address"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        phone = tracker.get_slot("phone_number")
        vendor_id = tracker.get_slot("vendor_id")
        new_address = tracker.get_slot("address")
        delivery_tag = tracker.get_slot("delivery_tag") or "home" # Default to 'home' if no tag is given

        if not phone or not vendor_id or not new_address:
            dispatcher.utter_message(text="I seem to be missing some information. I need your phone number and the new address.")
            return []
        
        success = CustomerService.update_customer_address(
            vendor_id=vendor_id, 
            phone_number=phone, 
            new_address=new_address, 
            tag=delivery_tag
        )

        if success:
            dispatcher.utter_message(text=f"Great! I've updated your '{delivery_tag}' address to: {new_address}")
        else:
            dispatcher.utter_message(text="Sorry, I couldn't find your profile to update the address. Please ensure you have a profile with us.")

        return [SlotSet("address", None), SlotSet("delivery_tag", None)] # Clear slots after use

class ActionSendPaymentInfo(Action):
    def name(self) -> Text:
        return "action_send_payment_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        #we will replace with real upi ID
        dispatcher.utter_message(text="Please send your payment to the UPI ID: example@upi or scan the QR code below.")
        #will add the qr code later
        return []
    
    
class ActionConfirmPurchase(Action):
    def name(self) -> Text:
        return "action_confirm_purchase"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        article_id = tracker.get_slot("article_id")
        delivery_tag = tracker.get_slot("delivery_tag")

        if article_id:
            dispatcher.utter_message(text=f"Great! Your order for article {article_id} is confirmed. 📦")
            if delivery_tag:
                dispatcher.utter_message(text=f"It will be delivered via {delivery_tag}.")
        else:
            dispatcher.utter_message(text="Could not confirm the purchase. Please provide the article ID.")

        return []