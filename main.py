import os
import json
import random
import datetime
import re

CONFIG_FILE = 'config.json'
DATA_FILE = 'flashcard_data.json'
FLASHCARD_DIR = 'flashcards'

SCORE_MAP = {'A': -2, 'S': -1, 'D': 1, 'F': 2}


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


def parse_markdown_files():
    cards = {}
    if not os.path.isdir(FLASHCARD_DIR):
        return cards
    current_cat = ''
    entry_re = re.compile(r'-\s*(.+?):\s*(.+?)\s*\[(.+?)\]\s*\[(.+?)\]')
    for fname in os.listdir(FLASHCARD_DIR):
        if not fname.endswith('.md'):
            continue
        with open(os.path.join(FLASHCARD_DIR, fname), 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    current_cat = line[1:].strip()
                elif line.startswith('-'):
                    m = entry_re.match(line)
                    if m:
                        jp, en, pron, hira = m.groups()
                        base_id = f"{fname}|{current_cat}|{jp}|{en}"
                        card_j2e = {
                            'id': base_id + '|J2E',
                            'front': jp,
                            'back': f"{en} [{pron}] [{hira}]",
                            'category': current_cat,
                            'deck': 'no_deck',
                            'ratings': [],
                            'skill': 0,
                            'struggle': 0,
                            'last_study': None
                        }
                        card_e2j = {
                            'id': base_id + '|E2J',
                            'front': en,
                            'back': f"{jp} [{pron}] [{hira}]",
                            'category': current_cat,
                            'deck': 'no_deck',
                            'ratings': [],
                            'skill': 0,
                            'struggle': 0,
                            'last_study': None
                        }
                        cards[card_j2e['id']] = card_j2e
                        cards[card_e2j['id']] = card_e2j
    return cards


def scan_files(data):
    new_cards = parse_markdown_files()
    for cid, card in new_cards.items():
        if cid not in data['cards']:
            data['cards'][cid] = card
        else:
            existing = data['cards'][cid]
            existing['front'] = card['front']
            existing['back'] = card['back']
            existing['category'] = card['category']
    save_data(data)
    print(f"Imported {len(new_cards)} cards. Total cards: {len(data['cards'])}")


def select_review_cards(data, count):
    review = [c for c in data['cards'].values() if c['deck'] == 'review']
    review.sort(key=lambda c: (-c['struggle'], c['last_study'] or 0))
    return [c['id'] for c in review[:count]]


def select_new_cards(data, count):
    no_deck = [c['id'] for c in data['cards'].values() if c['deck'] == 'no_deck']
    return no_deck[:count]


def start_new_day(data, config):
    # reset any existing study cards
    for cid in list(data['study_deck']):
        card = data['cards'][cid]
        card['ratings'] = []
        card['skill'] = 0
        card['struggle'] = 0
    # pull new cards
    for cid in select_new_cards(data, config['new_cards']):
        card = data['cards'][cid]
        card['deck'] = 'study'
        card['ratings'] = []
        card['skill'] = 0
        card['struggle'] = 0
        data['study_deck'].append(cid)
    # pull review cards
    for cid in select_review_cards(data, config['review_cards']):
        card = data['cards'][cid]
        card['deck'] = 'study'
        card['ratings'] = []
        card['skill'] = 0
        card['struggle'] = 0
        data['study_deck'].append(cid)
    data['last_session'] = str(datetime.date.today())
    save_data(data)
    print(f"New study session with {len(data['study_deck'])} cards.")


def show_card(card):
    print('\n---')
    print(f"Front: {card['front']}")
    input('Press Enter to reveal...')
    print(f"Back: {card['back']}")


def rate_card(card):
    while True:
        r = input('Rate (A=Wrong, S=Unsure, D=Correct, F=Easy): ').strip().upper()
        if r in SCORE_MAP:
            break
    card['ratings'].append(r)
    if len(card['ratings']) > 3:
        card['ratings'].pop(0)
    card['skill'] = sum(SCORE_MAP[x] for x in card['ratings'])
    if r == 'A':
        card['struggle'] += 3
    elif r == 'S':
        card['struggle'] += 1
    card['last_study'] = datetime.datetime.now().timestamp()


def study_session(data):
    if not data['study_deck']:
        print('No more cards!')
        return
    while data['study_deck']:
        cid = random.choice(data['study_deck'])
        card = data['cards'][cid]
        show_card(card)
        rate_card(card)
        if card['skill'] >= 2:
            card['deck'] = 'review'
            card['ratings'] = []
            card['skill'] = 0
            card['struggle'] = 0
            data['study_deck'].remove(cid)
        save_data(data)
    print('Study session complete!')


def main():
    config = load_config()
    data = load_data()
    if not data['cards']:
        scan_files(data)
    while True:
        print('\nMenu:')
        print('1) Study')
        print('2) Scan Files')
        print('3) New Day')
        print('4) Quit')
        choice = input('Select: ').strip()
        if choice == '1':
            study_session(data)
        elif choice == '2':
            scan_files(data)
        elif choice == '3':
            start_new_day(data, config)
        elif choice == '4':
            break
        else:
            print('Invalid choice')


if __name__ == '__main__':
    main()
