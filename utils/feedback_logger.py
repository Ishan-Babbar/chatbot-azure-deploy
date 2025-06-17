import os
import json
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure Blob Storage configuration
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("FEEDBACK_CONTAINER_NAME")
BLOB_NAME = "feedback.csv"

# Convert feedback data to a CSV row
def feedback_to_csv_row(data):
    return [
        data["timestamp"],
        data["strategy"],
        data["prompt_version"],
        data["model_name"],
        data["feedback"],
        data.get("title", ""),
        data.get("messages", "") # Full chat history as a plain text
    ]

# Upload or append feedback to Azure Blob Storage
def log_feedback_to_blob(feedback_data):
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    blob_client = container_client.get_blob_client(BLOB_NAME)

    # Prepare CSV row
    csv_row = feedback_to_csv_row(feedback_data)
    csv_line = ",".join(f'"{item}"' for item in csv_row) + "\n"

    # Check if blob exists
    try:
        existing_data = blob_client.download_blob().readall().decode("utf-8")
        updated_data = existing_data + csv_line
    except Exception:
        # If blob doesn't exist, create with header
        header = ["timestamp", "strategy", "prompt_version", "model_name", "feedback", "title", "chat_history"]
        updated_data = ",".join(header) + "\n" + csv_line

    # Upload updated content
    blob_client.upload_blob(updated_data, overwrite=True)
    print("✅ Feedback logged to Azure Blob Storage.")

# Public function to be imported
def log_feedback(strategy, prompt_version, model_name, feedback, title, messages):
    feedback_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "strategy": strategy,
        "prompt_version": prompt_version,
        "model_name": model_name,
        "feedback": feedback,
        "title": title,
        "messages": messages  # full chat history
    }
    log_feedback_to_blob(feedback_data)