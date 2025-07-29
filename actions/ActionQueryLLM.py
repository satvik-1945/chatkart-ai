import requests
from typing import Dict, Any,Text,List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

LLM_URL = "http://localhost:8000/chatbot/query"

class ActionQueryLLM(Action):

    def name(self) -> str:
        return "action_query_llm"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> list[Dict[str, Any]]:
        user_query = tracker.latest_message.get('text')
        context = {
            "vendor_id":tracker.get_slot("vendor_id"),
            "conversation":tracker.events
        }

        payload = {
            "user_query": user_query,
            "context": context
        }
        try:
            res = requests.post(LLM_URL, json=payload,timeout=10)
            res.raise_for_status()
            llm_response = res.json().get("response", "I couldn't process your request.")
        except requests.exceptions.RequestException as e:
            llm_response = f"Error communicating with LLM service: {str(e)}"
        
        dispatcher.utter_message(text=llm_response)
        return []