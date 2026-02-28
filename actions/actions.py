from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher  
from rasa_sdk.events import SlotSet, EventType, SessionStarted, ActionExecuted
from rasa_sdk.forms import FormValidationAction
from commons.utils.CustomerService import CustomerService
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
        """
        This method is called ONLY ONCE after all required slots are filled.
        It gathers the complete data and persists it in MongoDB.
        """
        try:
            logger.info("--- Form complete, entering submit method ---")
            
            vendor_id = tracker.get_slot("vendor_id")
            phone = tracker.get_slot("phone_number")

            if not vendor_id or not phone:
                logger.error(f"Critical data missing in submit. Vendor ID: {vendor_id}, Phone: {phone}")
                dispatcher.utter_message(text="Sorry, I'm missing some required information to save your profile.")
                return []

            customer_data = {
                "vendor_id": vendor_id,
                "name": tracker.get_slot("name"),
                "phone_number": phone,
                "address": tracker.get_slot("address"),
                "email": tracker.get_slot("email"),
            }
            logger.info(f"Complete customer data prepared: {customer_data}")

            logger.info("Calling CustomerService.add_customer...")
            success = CustomerService.add_customer(customer_data)

            if success:
                logger.info(f"Successfully added customer with phone: {phone}")
                dispatcher.utter_message(response="utter_profile_created", name=customer_data['name'])
                # On success, clear all the form slots
                return [SlotSet("name", None), SlotSet("phone_number", None), SlotSet("address", None), SlotSet("email", None)]
            else:
                logger.warning(f"CustomerService.add_customer returned False for phone: {phone}. Customer might already exist.")
                dispatcher.utter_message(text=f"It looks like the phone number {phone} is already registered with us. ⚠️")
                return []

        except Exception as e:
            logger.error(f"An unexpected error occurred in submit: {e}", exc_info=True)
            dispatcher.utter_message(text="I'm sorry, we've run into a technical issue and couldn't save your profile.")
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

