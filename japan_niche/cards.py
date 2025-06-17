import os
import re
import datetime
from .data import save_data

FLASHCARD_DIR = 'flashcards'
SCORE_MAP = {'A': -2, 'S': -1, 'D': 1, 'F': 2}


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
                        common = {
                            'jp': jp,
                            'en': en,
                            'pron': pron,
                            'hira': hira,
                            'category': current_cat,
                            'deck': 'no_deck',
                            'ratings': [],
                            'skill': 0,
                            'struggle': 0,
                            'last_study': None,
                        }
                        card_j2e = common.copy()
                        card_j2e.update({'id': base_id + '|J2E', 'front': jp, 'direction': 'J2E'})
                        card_e2j = common.copy()
                        card_e2j.update({'id': base_id + '|E2J', 'front': en, 'direction': 'E2J'})
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
            for k in ['front', 'jp', 'en', 'pron', 'hira', 'category']:
                existing[k] = card[k]
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
    for cid in list(data['study_deck']):
        card = data['cards'][cid]
        card['ratings'] = []
        card['skill'] = 0
        card['struggle'] = 0
    for cid in select_new_cards(data, config['new_cards']):
        card = data['cards'][cid]
        card['deck'] = 'study'
        card['ratings'] = []
        card['skill'] = 0
        card['struggle'] = 0
        data['study_deck'].append(cid)
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
