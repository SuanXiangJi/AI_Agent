from pathlib import Path
import json

def load_append_config():
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('common_append_text', [])
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return []

def load_inner_web_scale():
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('inner_web_scale', 1)  # 默认值设为 0.7
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return 0.7 
def get_config_value(key: str, sub_key: str = None): # 获取配置文件中的值
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if sub_key:
                return config.get(key, {}).get(sub_key)
            return config.get(key)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
