import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse

# Import your chatbot logic
try:
    from chat_code import ask_chatbot
except ImportError:
    # Fallback if chat_code.py is not available
    def ask_chatbot(message):
        return "This is a placeholder response. Please implement ask_chatbot in chat_code.py"

app = Flask(__name__)
CORS(app)  # Allow frontend to access this API

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])
    
    user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
    if not user_message:
        return jsonify({"error": "No user message found"}), 400

    try:
        reply = ask_chatbot(user_message)
        return jsonify({"reply": reply})
    except Exception as e:
        print("❌ Error in ask_chatbot:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    response = MessagingResponse()

    try:
        reply = ask_chatbot(incoming_msg)
        response.message(reply)
    except Exception as e:
        print("❌ Error in WhatsApp handler:", e)
        traceback.print_exc()
        response.message("Sorry, something went wrong.")

    return str(response)

if __name__ == "__main__":
    app.run(debug=True)