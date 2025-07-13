# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher  
from rasa_sdk.events import SlotSet

# in memory database for now 
USER_PROFILE = {}
ORDERS = {}

class ActionSaveProfile(Action):
    def name(self) -> Text:
        return "action_save_profile"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        name  = tracker.get_slot("name")
        phone = tracker.get_slot("phone_number")
        address = tracker.get_slot("address")
        email = tracker.get_slot("email")

        if name and phone:
            USER_PROFILE['name'] = name
            USER_PROFILE['phone'] = phone
            USER_PROFILE['address'] = address if address else "Not provided"
            USER_PROFILE['email'] = email if email else "Not provided"
            
            dispatcher.utter_message(text=f"Profile saved: {name}")
        else:
            dispatcher.utter_message(text="Please provide both name and phone number to save your profile.")

        return []
    
class ActionChangeAddress(Action):
    def name(self) ->Text:
        return "actions_change_address"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        phone = tracker.get_slot("phone_number")
        address = tracker.get_slot("address")
        delivery_address = tracker.get_slot("delivery_tag")

        if phone in USER_PROFILE:
            USER_PROFILE[phone]['address'] = address or USER_PROFILE[phone]["address"]
            tag = delivery_address or "home"
            USER_PROFILE[phone]['delivery_tag'] = tag
            dispatcher.utter_message(text=f"Address updated to: {USER_PROFILE[phone]['address']} with tag {tag}")
        else:
            dispatcher.utter_message(text="No profile found. Please create a profile first.")
        return []
    
class ActionSendPaymentInfo(Action):
    def name(self) -> Text:
        return "action_send_payment_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        #we will replace with real upi ID
        dispatcher.utter_message(text="Please send your payment to the UPI ID: example@upi or scan the QR code below.")
        #will add the qr code later
        return []
    
class ActionAnswerQueries(Action):
    def name(self) -> Text:
        return "action_answer_queries"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        query = tracker.latest_message.get('text', '')
        #TODO: add intent specific answer or retrival model
        dispatcher.utter_message(text=f"Thanks for your question. We will get back to you soon with an answer.")
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