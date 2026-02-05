import requests
import json
import os

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://ollama_server:11434")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "deepseek-r1:1.5b") 

full_api_url = f"{OLLAMA_API_URL}/api/generate"

OLLAMA_CONNECT_TIMEOUT_SECS = int(os.getenv("OLLAMA_CONNECT_TIMEOUT_SECS", "10"))
OLLAMA_READ_TIMEOUT_SECS = int(os.getenv("OLLAMA_READ_TIMEOUT_SECS", "120"))

def query_ollama(prompt: str, model: str = DEFAULT_LLM_MODEL) -> str:
    payload = {"model": model, "prompt": prompt, "stream": True}
    with requests.post(
        full_api_url,
        json=payload,
        stream=True,
        timeout=(OLLAMA_CONNECT_TIMEOUT_SECS, OLLAMA_READ_TIMEOUT_SECS),
    ) as r:
        if r.status_code != 200:
            return f"Ollama Error! Status: {r.status_code}, Response: {r.text}"

        output_text = ""
        for line in r.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    output_text += data["response"]
                if data.get("done"):
                    break

        return output_text.strip()
    
