import json
import os

DATA_FILE = 'flashcard_data.json'


def convert():
    if not os.path.exists(DATA_FILE):
        print('flashcard_data.json not found')
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Detect already converted format by ensuring *all* cards have simple
    # Japanese IDs (no `|` separator) and the ratings field is a dict. The
    # previous implementation only looked at a single card which caused a
    # mix of old and new formats to be incorrectly detected as converted.
    already_new = True
    for card in data.get('cards', {}).values():
        if not isinstance(card.get('ratings'), dict) or '|' in card.get('id', ''):
            already_new = False
            break
    if already_new:
        print('Data already in new format')
        return

    old_cards = data.get('cards', {})
    new_cards = {}
    id_map = {}

    for cid, card in old_cards.items():
        jp = card.get('jp')
        en = card.get('en')
        pron = card.get('pron')
        hira = card.get('hira')
        direction = card.get('direction', 'J2E')

        if not jp:
            continue

        new_id = jp
        target = new_cards.get(new_id)
        if target is None:
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
            new_cards[new_id] = target
        else:
            # Update details if present
            for k, v in [('en', en), ('pron', pron), ('hira', hira)]:
                if v:
                    target[k] = v
            if card.get('deck', 'no_deck') != 'no_deck':
                target['deck'] = card['deck']

        target['ratings'][direction] = card.get('ratings', [])
        target['skill'][direction] = card.get('skill', 0)
        target['struggle'][direction] = card.get('struggle', 0)
        target['last_study'][direction] = card.get('last_study')

        id_map[cid] = new_id

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
