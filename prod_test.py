import requests

# Replace this with your actual Azure Web App URL
url = "https://frog-research-chat-cuh5e2cufvcccthj.ukwest-01.azurewebsites.net/api/chat"

# Sample message payload
payload = {
    "messages": [
        {"role": "user", "content": "What is RAG in AI?"}
    ]
}

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    print("✅ Response from server:")
    print(response.json())
except requests.exceptions.RequestException as e:
    print("❌ Request failed:")
    print(e)