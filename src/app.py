# Clean version of app.py with chat title generation and readable history formatting

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from chat_code import ask_chatbot
from utils.feedback_logger import log_feedback
import os
import sys
import traceback
import datetime

# Add root to sys.path to access utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

def generate_chat_title(messages):
    first_user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    title = " ".join(first_user_msg.split()[:6]).replace("?", "").replace("!", "").strip()
    return title or f"Chat {datetime.datetime.now().strftime('%H:%M:%S')}"

def format_chat_history(messages):
    return "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in messages)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    if not user_message:
        return jsonify({"error": "No user message found"}), 400

    try:
        result = ask_chatbot(user_message, chat_history=messages)
        return jsonify({
            "reply": result["reply"],
            "references": result["references"]
        })
    except Exception as e:
        print("❌ Error in ask_chatbot:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/feedback", methods=["POST"])
def save_feedback():
    data = request.get_json()
    messages = data.get("messages", [])
    strategy = data.get("strategy", "cot")
    prompt_version = data.get("prompt_version", "v1")
    model_name = data.get("model_name", "gpt-4o-mini-voc2")
    feedback = data.get("feedback", "thumbs_up")
    title = data.get("title") or generate_chat_title(messages)

    formatted_history = format_chat_history(messages)
    print("📝 Chat Transcript:\n", formatted_history)

    try:
        log_feedback(
            strategy=strategy,
            prompt_version=prompt_version,
            model_name=model_name,
            feedback=feedback,
            title=title,
            messages=formatted_history
        )
        return jsonify({"status": "saved", "title": title})
    except Exception as e:
        print("❌ Error in log_feedback:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)