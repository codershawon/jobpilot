import httpx
from app.config import settings

url = "https://generativelanguage.googleapis.com/v1beta/models"
res = httpx.get(url, params={"key": settings.GEMINI_API_KEY}, timeout=20)

for m in res.json().get("models", []):
    if "generateContent" in m.get("supportedGenerationMethods", []):
        print(m["name"].replace("models/", ""))