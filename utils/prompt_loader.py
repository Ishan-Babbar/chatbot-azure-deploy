import json
import os

def load_prompt(version="v1"):
    prompt_path = os.path.join("prompts", f"{version}_prompt.json")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return json.load(f)