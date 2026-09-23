import requests

# Test health
response = requests.get("http://localhost:8000/health")
print("Health:", response.json())

# Test image search
with open("images/query.jpg", "rb") as f:
    files = {"image": ("query.jpg", f, "image/jpeg")}
    data = {"weight_image": 1.0, "weight_text": 0.0, "top_k": 5}
    response = requests.post("http://localhost:8000/search", files=files, data=data)
    print("Image search:", response.json())

# Test text search
data = {"text": "lost dog with blue collar", "weight_image": 0.0, "weight_text": 1.0, "top_k": 5}
response = requests.post("http://localhost:8000/search", data=data)
print("Text search:", response.json())