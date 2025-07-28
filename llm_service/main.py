from fastapi import FastAPI
from pydantic import BaseModel
from utils.ollama_client import query_ollama

app = FastAPI(title="Chatkart LLM Orchestrator")

class QueryRequest(BaseModel):
    user_query: str
    context: dict

class QueryResponse(BaseModel):
    response: str

@app.post("/chatbot/query", response_model=QueryResponse)
async def chatbot_query(request: QueryRequest):
    """
    Endpoint to handle user queries and return responses from the LLM.
    """
    # Extract user query and context from the request
    user_query = request.user_query
    context = request.context

    # Call the Ollama client to get the response
    prompt = f"User Query: {user_query}\nContext: {context}"
    response = query_ollama(prompt)

    return QueryResponse(response=response)