import requests 
import json
import os

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://ollama_server:11434")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "deepseek-r1:1.5b") 

full_api_url = f"{OLLAMA_API_URL}/api/generate"

def query_ollama(prompt: str, model:str = DEFAULT_LLM_MODEL) -> str:
    payload = {"model": model, "prompt": prompt, "stream": True}
    with requests.post(full_api_url, json=payload, stream=True) as r:
        if r.status_code != 200:
            return "Error: Failed to reach OLlama."
        
        output_text = ""
        for line in r.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    output_text += data["response"]
                if data.get("done"):
                    break

        return output_text.strip()
    