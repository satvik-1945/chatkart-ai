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

    return QueryResponse(**result)
