import json
import os
import urllib.request
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GOOGLE_API_URL = os.getenv(
    "GOOGLE_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
).strip()

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set in the environment. Copy .env.example to .env and add your key.")

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Test Google AI Studio API connection for DE-coded with CG content generation.",
                }
            ]
        }
    ]
}

request_data = json.dumps(payload).encode("utf-8")
request = urllib.request.Request(
    GOOGLE_API_URL,
    data=request_data,
    headers={
        "Content-Type": "application/json",
        "x-goog-api-key": GOOGLE_API_KEY,
    },
    method="POST",
)

print(f"Testing Google AI Studio API URL: {GOOGLE_API_URL}")
try:
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8")
        print("Response status:", response.status)
        print("Response body:")
        print(body)
except urllib.error.HTTPError as err:
    error_body = err.read().decode("utf-8", errors="ignore")
    print("HTTP Error:", err.code, err.reason)
    print("Response body:")
    print(error_body)
    raise
except urllib.error.URLError as err:
    print("URL Error:", err.reason)
    raise
