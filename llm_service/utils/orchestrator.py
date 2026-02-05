import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from commons.utils.InventoryService import InventoryService
from commons.utils.MongoDBClient import MongoDBClient

from utils.ollama_client import query_ollama


logger = logging.getLogger(__name__)

ARTICLE_ID_RE = re.compile(r"\b\d{1,2}[a-zA-Z]{3}\d{2}-\d{1,3}\b")


def orchestrate_user_query(user_query: str, context: Dict[str, Any], vendor_id: str) -> Dict[str, Any]:
    tool, args = _select_tool(user_query=user_query, context=context)

    if tool == "register_user":
        return {
            "response": "Sure, let's create your profile.",
            "next_action": "profile_form",
            "slots": None,
        }

    if tool == "payment":
        return {
            "response": "Payments are not enabled yet. If you'd like to place an order, tell me the product ID(s) and quantity and I'll help you confirm the order.",
            "next_action": None,
            "slots": None,
        }

    if tool == "check_inventory":
        try:
            response = _handle_check_inventory(vendor_id=vendor_id, user_query=user_query)
        except Exception:
            logger.exception("check_inventory failed", extra={"vendor_id": vendor_id})
            response = "I ran into an issue while checking the inventory. Please try again in a moment."
        return {
            "response": response,
            "next_action": None,
            "slots": None,
        }

    if tool == "make_catalog":
        try:
            response = _handle_make_catalog(vendor_id=vendor_id)
        except Exception:
            logger.exception("make_catalog failed", extra={"vendor_id": vendor_id})
            response = "I ran into an issue while generating the catalog. Please try again in a moment."
        return {
            "response": response,
            "next_action": None,
            "slots": None,
        }

    if tool == "lock_product":
        article_id = args.get("article_id")
        if not article_id:
            return {
                "response": "Which product would you like me to lock? Please share the product ID (example: 21may25-1).",
                "next_action": None,
                "slots": None,
            }

        try:
            response = _handle_lock_product(vendor_id=vendor_id, article_id=article_id)
        except Exception:
            logger.exception("lock_product failed", extra={"vendor_id": vendor_id, "article_id": article_id})
            response = "I ran into an issue while locking that product. Please try again in a moment."

        return {"response": response, "next_action": None, "slots": None}

    if tool == "show_product_by_id":
        article_id = args.get("article_id")
        if not article_id:
            return {
                "response": "Please share the product ID (example: 21may25-1).",
                "next_action": None,
                "slots": None,
            }

        return {
            "response": "Got it.",
            "next_action": "action_show_product_by_id",
            "slots": {"article_id": article_id},
        }

    prompt = _build_general_prompt(user_query=user_query, context=context, vendor_id=vendor_id)
    response = query_ollama(prompt)
    return {"response": response, "next_action": None, "slots": None}


def _select_tool(user_query: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    article_id = _extract_article_id(user_query)
    if article_id:
        return "show_product_by_id", {"article_id": article_id}

    heuristic = _select_tool_heuristic(user_query)
    if heuristic is not None:
        return heuristic

    llm_choice = _select_tool_llm(user_query=user_query, context=context)
    if llm_choice is not None:
        return llm_choice

    return "general_question", {}


def _extract_article_id(text: str) -> Optional[str]:
    match = ARTICLE_ID_RE.search(text or "")
    return match.group(0) if match else None


def _select_tool_heuristic(user_query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    text = (user_query or "").lower()

    if any(k in text for k in ["register", "sign up", "signup", "create profile", "create my profile", "create account"]):
        return "register_user", {}

    if any(k in text for k in ["pay", "payment", "checkout"]):
        return "payment", {}

    if any(k in text for k in ["inventory", "in stock", "available"]):
        return "check_inventory", {}

    if any(k in text for k in ["catalog", "show products", "product list", "list products"]):
        return "make_catalog", {}

    if any(k in text for k in ["lock", "reserve", "hold"]):
        article_id = _extract_article_id(user_query)
        return "lock_product", {"article_id": article_id} if article_id else {}

    return None


def _select_tool_llm(user_query: str, context: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    prompt = (
        "You are a routing layer for a commerce chatbot. "
        "Choose the single best tool for the user query and return only strict JSON.\n\n"
        "Tools:\n"
        "- register_user: start profile registration flow\n"
        "- payment: user wants to pay or checkout\n"
        "- check_inventory: user asks what is available / in stock\n"
        "- make_catalog: user wants a list of products\n"
        "- lock_product: reserve/hold a product; requires article_id\n"
        "- show_product_by_id: show details of a product; requires article_id\n"
        "- general_question: everything else\n\n"
        "Return JSON with shape: {\"tool\": <tool_name>, \"arguments\": { ... }}.\n\n"
        f"User query: {user_query}\n"
        f"Context (may be empty): {context}"
    )

    raw = query_ollama(prompt)
    parsed = _try_parse_json_object(raw)
    if not parsed:
        return None

    tool = parsed.get("tool")
    args = parsed.get("arguments")
    if not isinstance(tool, str) or not isinstance(args, dict):
        return None

    allowed = {
        "register_user",
        "payment",
        "check_inventory",
        "make_catalog",
        "lock_product",
        "show_product_by_id",
        "general_question",
    }
    if tool not in allowed:
        return None

    return tool, args


def _try_parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    try:
        loaded = json.loads(text)
        return loaded if isinstance(loaded, dict) else None
    except Exception:
        pass

    codeblock_match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if codeblock_match:
        try:
            loaded = json.loads(codeblock_match.group(1))
            return loaded if isinstance(loaded, dict) else None
        except Exception:
            return None

    return None


def _handle_check_inventory(vendor_id: str, user_query: str) -> str:
    inventory = InventoryService.get_vendor_inventory(vendor_id)
    if not inventory:
        return "I couldn't find any inventory for this vendor yet."

    filtered = _filter_inventory(inventory, user_query)
    items = filtered[:5]

    if not items:
        return "I couldn't find a matching product in the inventory. Try asking for a product ID (example: 21may25-1) or ask for the catalog."

    lines = ["Here are a few matching items:"]
    for item in items:
        name = item.get("name", "Unnamed")
        article_id = item.get("article_id", "")
        price = item.get("price")
        price_text = f"${price}" if price is not None else ""
        lines.append(f"- {name} ({article_id}) {price_text}".strip())
    return "\n".join(lines)


def _handle_make_catalog(vendor_id: str) -> str:
    inventory = InventoryService.get_vendor_inventory(vendor_id)
    if not inventory:
        return "I couldn't find any products for this vendor yet."

    lines = ["Here is the catalog:"]
    for item in inventory[:10]:
        name = item.get("name", "Unnamed")
        article_id = item.get("article_id", "")
        price = item.get("price")
        price_text = f"${price}" if price is not None else ""
        lines.append(f"- {name} ({article_id}) {price_text}".strip())
    return "\n".join(lines)


def _handle_lock_product(vendor_id: str, article_id: str) -> str:
    now = datetime.utcnow()
    lock_until = now + timedelta(minutes=15)

    inventory = MongoDBClient.get_collection("inventory")
    result = inventory.update_one(
        {
            "vendor_id": vendor_id,
            "article_id": article_id,
            "$or": [
                {"locked_until": {"$exists": False}},
                {"locked_until": {"$lte": now}},
            ],
        },
        {
            "$set": {
                "locked_until": lock_until,
                "locked_at": now,
            }
        },
    )

    if result.matched_count == 0:
        return f"I couldn't find product '{article_id}' for this vendor."

    if result.modified_count == 0:
        return f"That product is currently locked. Please try again in a few minutes."

    return f"Locked {article_id} for 15 minutes. If you'd like to proceed, tell me the quantity you want."


def _filter_inventory(inventory: list, user_query: str) -> list:
    terms = _extract_query_terms(user_query)
    if not terms:
        return inventory

    def matches(item: dict) -> bool:
        hay = f"{item.get('name', '')} {item.get('description', '')}".lower()
        return all(term in hay for term in terms)

    return [i for i in inventory if matches(i)]


def _extract_query_terms(user_query: str) -> list[str]:
    text = (user_query or "").lower()
    words = re.findall(r"[a-z0-9]+", text)
    stop = {
        "is",
        "are",
        "the",
        "a",
        "an",
        "to",
        "in",
        "on",
        "for",
        "of",
        "with",
        "and",
        "or",
        "have",
        "has",
        "do",
        "you",
        "i",
        "we",
        "me",
        "my",
        "our",
        "inventory",
        "available",
        "stock",
        "catalog",
        "products",
        "product",
        "list",
        "show",
    }
    return [w for w in words if w not in stop][:4]


def _build_general_prompt(user_query: str, context: Dict[str, Any], vendor_id: str) -> str:
    return (
        "You are ChatKart AI. Answer the user query for vendor-specific commerce assistance. "
        "If you do not have enough information, ask a short clarifying question.\n\n"
        f"Vendor ID: {vendor_id}\n"
        f"User query: {user_query}\n"
        f"Context: {context}"
    )
