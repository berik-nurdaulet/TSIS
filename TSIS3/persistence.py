import json
import os

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "red",
    "difficulty": "medium"
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # merge with defaults in case new keys added
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_leaderboard(entries):
    # Sort by score desc, keep top 10
    entries = sorted(entries, key=lambda x: x["score"], reverse=True)[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(entries, f, indent=2)
    return entries

def add_leaderboard_entry(name, score, distance, coins):
    entries = load_leaderboard()
    entries.append({
        "name": name,
        "score": score,
        "distance": distance,
        "coins": coins
    })
    return save_leaderboard(entries)