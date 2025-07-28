import requests 
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def query_ollama(prompt: str, model:str = "deepseek-r1:1.5b") -> str:
    payload = {"model": model, "prompt": prompt, "stream": True}
    with requests.post(OLLAMA_API_URL, json=payload, stream=True) as r:
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
    