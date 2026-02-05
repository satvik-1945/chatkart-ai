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

        max_messages = 5
        max_len = 512
        recent_user_messages: List[str] = []
        for e in reversed(tracker.events):
            event_type = None
            text = None

            if isinstance(e, dict):
                event_type = e.get("event")
                text = e.get("text")
            else:
                event_type = getattr(e, "event", None)
                text = getattr(e, "text", None)
                as_dict = getattr(e, "as_dict", None)
                if callable(as_dict):
                    try:
                        d = as_dict()
                    except Exception:
                        d = None
                    if isinstance(d, dict):
                        event_type = event_type or d.get("event")
                        text = text or d.get("text")

            if event_type != "user":
                continue
            if isinstance(text, str) and text:
                recent_user_messages.append(text[:max_len])
                if len(recent_user_messages) >= max_messages:
                    break

        recent_user_messages.reverse()

        allowed_context_slots = {"vendor_id", "article_id"}
        slot_values = {
            k: v
            for k, v in tracker.current_slot_values().items()
            if k in allowed_context_slots
        }

        payload = {
            "user_query": user_query,
            "vendor_id": vendor_id,
            "context": {
                "recent_user_messages": recent_user_messages,
                "slots": slot_values,
            },
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

        if not isinstance(body, dict):
            logger.error(
                "Unexpected JSON type from LLM service",
                extra={"status_code": res.status_code, "body_type": type(body).__name__},
            )
            dispatcher.utter_message(text="I couldn't process the response from the AI service. Please try again.")
            return []

        llm_response = body.get("response")
        if not isinstance(llm_response, str):
            llm_response = ""
        next_action = body.get("next_action")
        slots = body.get("slots")

        events: List[Dict[str, Any]] = []
        allowed_slots = {"article_id"}
        if isinstance(slots, dict):
            for k, v in slots.items():
                if k in allowed_slots:
                    events.append(SlotSet(k, v))
                else:
                    logger.warning("Ignoring unexpected slot from LLM", extra={"slot": k})

        allowed_actions = {"action_show_product_by_id", "profile_form"}
        if isinstance(next_action, str) and next_action:
            if next_action in allowed_actions:
                events.append(FollowupAction(next_action))
            else:
                logger.warning("Ignoring unexpected next_action from LLM", extra={"next_action": next_action})

        if not llm_response and isinstance(next_action, str) and next_action in allowed_actions:
            llm_response = "Got it, let me handle that for you."
        if not llm_response:
            llm_response = "I couldn't process your request."

        dispatcher.utter_message(text=llm_response)

        return events
