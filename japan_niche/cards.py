import os
import re
import datetime
from .data import save_data

FLASHCARD_DIR = 'flashcards'
SCORE_MAP = {'A': -2, 'S': -1, 'D': 1, 'F': 2}


def parse_markdown_files(existing_ids=None):
    """Parse markdown files into card objects.

    Parameters
    ----------
    existing_ids : Iterable[str], optional
        Set of ids that already exist in the data file so we can avoid
        collisions when generating ids for duplicate cards.
    """
    if existing_ids is None:
        existing_ids = set()
    cards = {}
    if not os.path.isdir(FLASHCARD_DIR):
        return cards

    entry_re = re.compile(r'-\s*(.+?):\s*(.+?)\s*\[(.+?)\]\s*\[(.+?)\]')
    for fname in os.listdir(FLASHCARD_DIR):
        if not fname.endswith('.md'):
            continue
        with open(os.path.join(FLASHCARD_DIR, fname), 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    # category headers are ignored in the new format
                    continue
                if line.startswith('-'):
                    m = entry_re.match(line)
                    if not m:
                        continue
                    jp, en, pron, hira = m.groups()
                    base_id = f"{jp}|{en}"
                    cid = base_id
                    while cid in existing_ids or cid in cards:
                        cid += '*'

                    cards[cid] = {
                        'id': cid,
                        'jp': jp,
                        'en': en,
                        'pron': pron,
                        'hira': hira,
                        'deck': 'no_deck',
                        'ratings': {'J2E': [], 'E2J': []},
                        'skill': {'J2E': 0, 'E2J': 0},
                        'struggle': {'J2E': 0, 'E2J': 0},
                        'last_study': {'J2E': None, 'E2J': None},
                    }
    return cards


def scan_files(data):
    """Read markdown files and merge cards into *data*."""
    new_cards = parse_markdown_files(existing_ids=set(data['cards'].keys()))
    for cid, card in new_cards.items():
        if cid not in data['cards']:
            data['cards'][cid] = card
        else:
            existing = data['cards'][cid]
            for k in ['jp', 'en', 'pron', 'hira']:
                existing[k] = card[k]
    save_data(data)
    print(f"Imported {len(new_cards)} cards. Total cards: {len(data['cards'])}")


def _total_struggle(card):
    return card['struggle']['J2E'] + card['struggle']['E2J']


def _last_study(card):
    times = [t for t in card['last_study'].values() if t is not None]
    return min(times) if times else 0


def select_review_cards(data, count):
    review = [c for c in data['cards'].values() if c['deck'] == 'review']
    review.sort(key=lambda c: (-_total_struggle(c), _last_study(c)))
    return [c['id'] for c in review[:count]]


def select_new_cards(data, count):
    no_deck = [c['id'] for c in data['cards'].values() if c['deck'] == 'no_deck']
    return no_deck[:count]


def start_new_day(data, config):
    for cid in list(data['study_deck']):
        card = data['cards'][cid]
        card['ratings'] = {'J2E': [], 'E2J': []}
        card['skill'] = {'J2E': 0, 'E2J': 0}
        card['struggle'] = {'J2E': 0, 'E2J': 0}
    for cid in select_new_cards(data, config['new_cards']):
        card = data['cards'][cid]
        card['deck'] = 'study'
        card['ratings'] = {'J2E': [], 'E2J': []}
        card['skill'] = {'J2E': 0, 'E2J': 0}
        card['struggle'] = {'J2E': 0, 'E2J': 0}
        data['study_deck'].append(cid)
    for cid in select_review_cards(data, config['review_cards']):
        card = data['cards'][cid]
        card['deck'] = 'study'
        card['ratings'] = {'J2E': [], 'E2J': []}
        card['skill'] = {'J2E': 0, 'E2J': 0}
        card['struggle'] = {'J2E': 0, 'E2J': 0}
        data['study_deck'].append(cid)
    data['last_session'] = str(datetime.date.today())
    save_data(data)
    print(f"New study session with {len(data['study_deck'])} cards.")
