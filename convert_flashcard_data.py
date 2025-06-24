import json
import os

DATA_FILE = 'flashcard_data.json'


def convert():
    if not os.path.exists(DATA_FILE):
        print('flashcard_data.json not found')
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Detect already converted format
    sample = next(iter(data.get('cards', {}).values()), None)
    if sample and isinstance(sample.get('ratings'), dict):
        print('Data already in new format')
        return

    old_cards = data.get('cards', {})
    new_cards = {}
    pair_map = {}
    id_map = {}

    for cid, card in old_cards.items():
        jp = card.get('jp')
        en = card.get('en')
        pron = card.get('pron')
        hira = card.get('hira')
        direction = card.get('direction', 'J2E')
        base_key = f"{jp}|{en}"
        lst = pair_map.setdefault(base_key, [])

        target = None
        for c in lst:
            if not c['ratings'][direction]:
                target = c
                break
        if target is None:
            idx = len(lst)
            new_id = base_key + ('*' * idx if idx else '')
            target = {
                'id': new_id,
                'jp': jp,
                'en': en,
                'pron': pron,
                'hira': hira,
                'deck': card.get('deck', 'no_deck'),
                'ratings': {'J2E': [], 'E2J': []},
                'skill': {'J2E': 0, 'E2J': 0},
                'struggle': {'J2E': 0, 'E2J': 0},
                'last_study': {'J2E': None, 'E2J': None},
            }
            lst.append(target)
            new_cards[new_id] = target
        target['ratings'][direction] = card.get('ratings', [])
        target['skill'][direction] = card.get('skill', 0)
        target['struggle'][direction] = card.get('struggle', 0)
        target['last_study'][direction] = card.get('last_study')
        if card.get('deck', 'no_deck') != 'no_deck':
            target['deck'] = card['deck']
        id_map[cid] = target['id']

    new_study_deck = []
    for cid in data.get('study_deck', []):
        nid = id_map.get(cid)
        if nid and nid not in new_study_deck:
            new_study_deck.append(nid)

    new_data = {
        'cards': new_cards,
        'study_deck': new_study_deck,
        'last_session': data.get('last_session'),
    }

    backup = DATA_FILE + '.bak'
    os.rename(DATA_FILE, backup)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=4)
    print(f'Converted {len(old_cards)} cards to {len(new_cards)} cards.')
    print(f'Backup created at {backup}')


if __name__ == '__main__':
    convert()
