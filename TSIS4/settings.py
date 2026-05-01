# settings.py — load / save user preferences

import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULTS = {
    "snake_color": [50, 200, 50],   # RGB list
    "grid_overlay": False,
    "sound": True,
}


def load() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            # Fill in any missing keys with defaults
            for key, val in DEFAULTS.items():
                data.setdefault(key, val)
            return data
        except Exception as e:
            print(f"[Settings] load error: {e}")
    return dict(DEFAULTS)


def save(settings: dict) -> None:
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"[Settings] save error: {e}")