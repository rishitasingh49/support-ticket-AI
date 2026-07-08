import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY) if API_KEY else None

MODEL_NAME = "llama-3.1-8b-instant"
def ask_llm(prompt: str, system: str = "") -> str:
    if client is None:
        return "LLM_ERROR: GROQ_API_KEY is not set. Add it to your .env file."

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM_ERROR: {e}"