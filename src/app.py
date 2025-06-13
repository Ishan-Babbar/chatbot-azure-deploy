import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from chat_code import ask_chatbot

app = Flask(__name__)
CORS(app)  # Allow frontend to access this API

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])
    
    # Extract the latest user message
    user_message = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            user_message = msg["content"]
            break

    if not user_message:
        return jsonify({"error": "No user message found"}), 400

    try:
        reply = ask_chatbot(user_message)
        return jsonify({"reply": reply})
    except Exception as e:
        print("❌ Error in ask_chatbot:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host= "0:0:0:0", port=8000)