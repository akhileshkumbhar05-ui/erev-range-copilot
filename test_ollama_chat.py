import requests
import json

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "llama3.2:1b"   # same as you pulled

def ask_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Chat endpoint returns: {"message": {"content": ...}, "done": true, ...}
    return data["message"]["content"]

if __name__ == "__main__":
    answer = ask_ollama("Give me one sentence about extended-range EVs.")
    print("ANSWER:\n", answer)
