import sys
import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from .chat_code import ask_chatbot

# Add root to sys.path to access utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Serve the frontend
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# Serve static assets (CSS, JS, etc.)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Chat API endpoint
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

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
    app.run(host="0.0.0.0", port=8000)