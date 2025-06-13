import csv
import os
from datetime import datetime

FEEDBACK_DIR = "feedback"
os.makedirs(FEEDBACK_DIR, exist_ok=True)
FEEDBACK_LOG_PATH = os.path.join(FEEDBACK_DIR, "feedback_log.csv")

def log_feedback(user_query, model_response, strategy, prompt_version, model_name, feedback):
    feedback_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": user_query,
        "response": model_response,
        "strategy": strategy,
        "prompt_version": prompt_version,
        "model": model_name,
        "feedback": feedback
    }
    with open(FEEDBACK_LOG_PATH, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=feedback_data.keys())
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow(feedback_data)