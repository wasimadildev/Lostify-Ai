import requests
import json

# 1. Health check
try:
    print("Testing /health...")
    r = requests.get("http://localhost:8000/health", timeout=3)
    print(f"Status: {r.status_code}")
    print(r.json())
except Exception as e:
    print(f"❌ Health error: {e}")

print("\n" + "-" * 40)

# 2. Text-only search (no file upload, simplest)
try:
    print("Testing /search (text only)...")
    data = {"text": "lost dog", "weight_image": 0.0, "weight_text": 1.0, "top_k": 3}
    r = requests.post("http://localhost:8000/search", data=data, timeout=10)
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"❌ Search error: {e}")