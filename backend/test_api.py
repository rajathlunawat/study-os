import requests

base_url = "https://study-os-bk44.onrender.com"
print("Testing Chat Endpoint...")
try:
    res = requests.post(
        f"{base_url}/api/chat",
        json={"message": "give me short summary", "document_ids": []}
    )
    print("Status:", res.status_code)
    print("Response:", res.json())
except Exception as e:
    print("Error:", e)
