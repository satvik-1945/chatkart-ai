from fastapi import FastAPI
from pydantic import BaseModel
from utils.ollama_client import query_ollama

app = FastAPI(title="Chatkart LLM Orchestrator")

class QueryRequest(BaseModel):
    user_query: str
    context: dict
    vendor_id: str 

class QueryResponse(BaseModel):
    response: str

@app.post("/chatbot/query", response_model=QueryResponse)
async def chatbot_query(request: QueryRequest):
    user_query = request.user_query
    context = request.context
    vendor_id = request.vendor_id

    prompt = f"User Query: {user_query}\nContext: {context}"
    response = query_ollama(prompt)

    return QueryResponse(response=response)