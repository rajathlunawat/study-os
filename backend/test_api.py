import requests

base_url = "https://study-os-bk44.onrender.com"

print("1. Health Check (shows Gemini status)...")
try:
    res = requests.get(f"{base_url}/health", timeout=30)
    print("Status:", res.status_code)
    print("Response:", res.json())
except Exception as e:
    print("Error:", e)
