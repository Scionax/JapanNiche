import os
import json

CONFIG_FILE = 'config.json'
DATA_FILE = 'flashcard_data.json'


def load_config():
    if not os.path.exists(CONFIG_FILE):
        config = {"new_cards": 35, "review_cards": 100, "window_size": [80, 24]}
        save_config(config)
    else:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    return config


def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"cards": {}, "study_deck": [], "last_session": None}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
