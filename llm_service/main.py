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
    result = await to_thread.run_sync(
        partial(
            orchestrate_user_query,
            user_query=request.user_query,
            context=request.context,
            vendor_id=request.vendor_id,
        )
    )

    return QueryResponse(**result)
