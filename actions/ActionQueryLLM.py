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

        max_messages = 8
        max_len = 512
        recent_messages: List[Dict[str, str]] = []
        for e in reversed(tracker.events):
            event_type = None
            text = None

            if isinstance(e, dict):
                event_type = e.get("event")
                text = e.get("text")
            else:
                event_type = getattr(e, "event", None)
                text = getattr(e, "text", None)

            if event_type not in {"user", "bot"}:
                continue
            if isinstance(text, str) and text:
                role = "user" if event_type == "user" else "bot"
                recent_messages.append({"role": role, "text": text[:max_len]})
                if len(recent_messages) >= max_messages:
                    break

        recent_messages.reverse()
        recent_user_messages = [m["text"] for m in recent_messages if m.get("role") == "user"]

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
                "recent_messages": recent_messages,
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
        except requests.exceptions.RequestException:
            logger.exception("Error communicating with LLM service")
            dispatcher.utter_message(text="I'm having trouble reaching the AI service right now. Please try again in a moment.")
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
