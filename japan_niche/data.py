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
        data = json.load(f)
    if _upgrade_data_format(data):
        save_data(data)
    return data


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def _upgrade_data_format(data):
    """Migrate cards from the old 'front/back' format to the new fields."""
    changed = False
    cards = data.get('cards', {})
    for card in cards.values():
        # ------------------------------------------------------------------
        # Convert the original front/back format (pre refactor) to the new
        # explicit field format (jp/en/pron/hira) used by the GUI.  These old
        # cards stored all of their information in the ``id`` and ``back``
        # fields.
        # ------------------------------------------------------------------
        if 'jp' not in card or 'en' not in card:
            parts = card.get('id', '').split('|')
            if len(parts) >= 5:
                jp = parts[2]
                en = parts[3]
                direction = parts[4]
            else:
                continue
            back = card.get('back', '')
            import re
            m = re.match(r"(.+?)\s*\[(.+?)\]\s*\[(.+?)\]", back)
            if not m:
                continue
            val1, pron, hira = m.groups()
            if direction == 'J2E':
                en = val1
            else:
                jp = val1
            card.update({
                'jp': jp,
                'en': en,
                'pron': pron,
                'hira': hira,
                'direction': direction,
                'front': jp if direction == 'J2E' else en,
            })
            changed = True

        # ------------------------------------------------------------------
        # Convert rating/skill/struggle fields from a single direction list
        # into the newer per-direction dictionaries.  Older versions of the
        # program kept ``ratings`` as a list and ``skill``/``struggle`` as
        # integers keyed by ``direction``.  The GUI expects dictionaries so
        # upgrade the structure if necessary.
        # ------------------------------------------------------------------
        if not isinstance(card.get('ratings'), dict):
            direction = card.get('direction', 'J2E')
            ratings = card.get('ratings', [])
            skill = card.get('skill', 0)
            struggle = card.get('struggle', 0)
            last = card.get('last_study')

            card['ratings'] = {'J2E': [], 'E2J': []}
            card['ratings'][direction] = ratings

            card['skill'] = {'J2E': 0, 'E2J': 0}
            card['skill'][direction] = skill

            card['struggle'] = {'J2E': 0, 'E2J': 0}
            card['struggle'][direction] = struggle

            card['last_study'] = {'J2E': None, 'E2J': None}
            card['last_study'][direction] = last

            changed = True
    return changed
