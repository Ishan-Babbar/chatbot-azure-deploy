from loguru import logger
import os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger.add(os.path.join(LOG_DIR, "chatbot.log"), rotation="1 MB", retention="10 days")

def log_interaction(user_query, strategy, response, prompt_version, model_name, tokens_used=None):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": user_query,
        "strategy": strategy,
        "response": response,
        "prompt_version": prompt_version,
        "model": model_name,
        "tokens_used": tokens_used
    }
    logger.info(log_data)

def log_error(error_message, context=None):
    logger.error({
        "timestamp": datetime.utcnow().isoformat(),
        "error": error_message,
        "context": context
    })