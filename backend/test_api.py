import requests

base_url = "https://study-os-bk44.onrender.com"

print("1. Testing Health Check...")
try:
    res = requests.get(f"{base_url}/health")
    print("Status:", res.status_code)
    print("Response:", res.json())
except Exception as e:
    print("Error:", e)

print("\n2. Testing Chat Endpoint...")
try:
    res = requests.post(
        f"{base_url}/api/chat",
        json={"message": "What is thermodynamics?", "document_ids": []}
    )
    print("Status:", res.status_code)
    print("Response:", res.json())
except Exception as e:
    print("Error:", e)
