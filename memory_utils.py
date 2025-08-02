import json
from pathlib import Path

MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)

def get_memory_path(agent_type):
    return MEMORY_DIR / f"{agent_type}_chat.jsonl"

def load_memory(agent_type):
    path = get_memory_path(agent_type)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def save_message(agent_type, role, message):
    path = get_memory_path(agent_type)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"role": role, "message": message}) + "\n")