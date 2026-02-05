from functools import partial

from anyio import to_thread
from fastapi import FastAPI
from pydantic import BaseModel

from utils.orchestrator import orchestrate_user_query

app = FastAPI(title="Chatkart LLM Orchestrator")

class QueryRequest(BaseModel):
    user_query: str
    context: dict
    vendor_id: str 

class QueryResponse(BaseModel):
    response: str
    next_action: str | None = None
    slots: dict | None = None

@app.post("/chatbot/query", response_model=QueryResponse)
async def chatbot_query(request: QueryRequest):
    # `orchestrate_user_query` uses blocking IO (requests/pymongo), so we run it in a worker
    # thread to keep the FastAPI event loop responsive.
    result = await to_thread.run_sync(
        partial(
            orchestrate_user_query,
            user_query=request.user_query,
            context=request.context,
            vendor_id=request.vendor_id,
        )
    )

    if not isinstance(result, dict):
        result = {"response": str(result)}

    response = result.get("response")
    if not isinstance(response, str):
        result["response"] = str(response or "") or "I couldn't process your request."

    allowed_actions = {"action_show_product_by_id", "profile_form"}
    next_action = result.get("next_action")
    if next_action not in allowed_actions:
        result["next_action"] = None

    allowed_slot_keys = {"article_id"}
    slots = result.get("slots")
    if not isinstance(slots, dict):
        result["slots"] = None
    else:
        filtered_slots = {k: v for k, v in slots.items() if k in allowed_slot_keys}
        result["slots"] = filtered_slots or None

    return QueryResponse(**result)
