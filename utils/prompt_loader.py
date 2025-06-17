import os
import json

def load_prompt(version="v1"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    prompt_path = os.path.join(base_dir, 'prompts', f'{version}_prompts.json')

    with open(prompt_path, "r", encoding="utf-8") as f:
        return json.load(f)