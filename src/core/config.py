import os
import json
import logging

logger = logging.getLogger("PrivaSub.Config")

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "max_history_lines": 500,
    "auto_hide_timeout_s": 15,
    "opacity": 80,
    "target_language": "None (English Only)"
}

class AppConfig:
    @staticmethod
    def _get_config_path():
        # Store config next to main.py or project root
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), CONFIG_FILE)

    @staticmethod
    def load():
        path = AppConfig._get_config_path()
        config = DEFAULT_CONFIG.copy()
        
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    config.update(user_config)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        return config

    @staticmethod
    def save(config_dict):
        path = AppConfig._get_config_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
