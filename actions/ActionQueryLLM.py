import logging
import requests
from typing import Any, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import FollowupAction, SlotSet

LLM_URL = "http://llm_service:8000/chatbot/query" 

logger = logging.getLogger(__name__)

class ActionQueryLLM(Action):

    def name(self) -> str:
        return "action_query_llm"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        user_query = tracker.latest_message.get('text')
        vendor_id = tracker.get_slot("vendor_id")
        
        if not vendor_id:
            dispatcher.utter_message(text="Sorry, I need a vendor ID to proceed.")
            return []

        payload = {
            "user_query": user_query,
            "vendor_id": vendor_id,
            "context": {
                "conversation_events": tracker.events[-5:]
            }
        }
        try:
            res = requests.post(LLM_URL, json=payload, timeout=120)
            res.raise_for_status()
            try:
                body = res.json() or {}
            except ValueError:
                logger.exception("Invalid JSON from LLM service", extra={"status_code": res.status_code})
                dispatcher.utter_message(text="I couldn't process the response from the AI service. Please try again.")
                return []
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text=f"Error communicating with LLM service: {str(e)}")
            return []

        llm_response = body.get("response", "I couldn't process your request.")
        next_action = body.get("next_action")
        slots = body.get("slots")

        events: List[Dict[str, Any]] = []
        if isinstance(slots, dict):
            for k, v in slots.items():
                events.append(SlotSet(k, v))

        if llm_response:
            dispatcher.utter_message(text=llm_response)

        if isinstance(next_action, str) and next_action:
            events.append(FollowupAction(next_action))

        return events
