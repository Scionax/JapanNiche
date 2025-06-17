import os
import json
import random
import datetime
import re
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QStackedWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

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
    """CLI study session (retained for compatibility)."""
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


def cli_main():
    """Run the legacy command line interface."""
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


class StudyWidget(QWidget):
    """Widget used for the study session."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cid = None
        self.card = None

        self.front_label = QLabel()
        self.front_label.setAlignment(Qt.AlignCenter)
        self.front_label.setFont(QFont('Arial', 20))

        self.back_label = QLabel()
        self.back_label.setAlignment(Qt.AlignCenter)
        self.back_label.setFont(QFont('Arial', 18))

        self.show_btn = QPushButton('Show Answer')

        rating_layout = QHBoxLayout()
        self.btn_wrong = QPushButton('Wrong')
        self.btn_unsure = QPushButton('Unsure')
        self.btn_correct = QPushButton('Correct')
        self.btn_easy = QPushButton('Easy')
        for btn in (
            self.btn_wrong,
            self.btn_unsure,
            self.btn_correct,
            self.btn_easy,
        ):
            btn.setEnabled(False)
            rating_layout.addWidget(btn)

        layout = QVBoxLayout()
        layout.addWidget(self.front_label)
        layout.addWidget(self.back_label)
        layout.addWidget(self.show_btn)
        layout.addLayout(rating_layout)
        self.setLayout(layout)

        self.show_btn.clicked.connect(self.show_answer)
        self.btn_wrong.clicked.connect(lambda: self.rate('A'))
        self.btn_unsure.clicked.connect(lambda: self.rate('S'))
        self.btn_correct.clicked.connect(lambda: self.rate('D'))
        self.btn_easy.clicked.connect(lambda: self.rate('F'))

    def start_session(self):
        self.next_card()

    def next_card(self):
        if not self.main_window.data['study_deck']:
            QMessageBox.information(self, 'Done', 'Study session complete!')
            self.main_window.show_menu()
            return
        self.cid = random.choice(self.main_window.data['study_deck'])
        self.card = self.main_window.data['cards'][self.cid]
        self.front_label.setText(self.card['front'])
        self.back_label.setText('')
        self.show_btn.setEnabled(True)
        for btn in (
            self.btn_wrong,
            self.btn_unsure,
            self.btn_correct,
            self.btn_easy,
        ):
            btn.setEnabled(False)

    def show_answer(self):
        self.back_label.setText(self.card['back'])
        self.show_btn.setEnabled(False)
        for btn in (
            self.btn_wrong,
            self.btn_unsure,
            self.btn_correct,
            self.btn_easy,
        ):
            btn.setEnabled(True)

    def rate(self, rating):
        card = self.card
        card['ratings'].append(rating)
        if len(card['ratings']) > 3:
            card['ratings'].pop(0)
        card['skill'] = sum(SCORE_MAP[x] for x in card['ratings'])
        if rating == 'A':
            card['struggle'] += 3
        elif rating == 'S':
            card['struggle'] += 1
        card['last_study'] = datetime.datetime.now().timestamp()
        if card['skill'] >= 2:
            card['deck'] = 'review'
            card['ratings'] = []
            card['skill'] = 0
            card['struggle'] = 0
            self.main_window.data['study_deck'].remove(self.cid)
        save_data(self.main_window.data)
        self.next_card()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.data = load_data()
        if not self.data['cards']:
            scan_files(self.data)

        self.setWindowTitle('Japanese Flashcards')

        self.stack = QStackedWidget()
        self.menu_widget = self.create_menu()
        self.study_widget = StudyWidget(self)
        self.stack.addWidget(self.menu_widget)
        self.stack.addWidget(self.study_widget)
        self.setCentralWidget(self.stack)

    def create_menu(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addStretch()
        btn_study = QPushButton('Study')
        btn_scan = QPushButton('Scan Files')
        btn_new_day = QPushButton('New Day')
        btn_quit = QPushButton('Quit')
        for btn in (btn_study, btn_scan, btn_new_day, btn_quit):
            btn.setMinimumHeight(40)
            layout.addWidget(btn)
        layout.addStretch()
        widget.setLayout(layout)

        btn_study.clicked.connect(self.start_study)
        btn_scan.clicked.connect(self.scan_files)
        btn_new_day.clicked.connect(self.new_day)
        btn_quit.clicked.connect(self.close)
        return widget

    def show_menu(self):
        self.stack.setCurrentWidget(self.menu_widget)

    def start_study(self):
        if not self.data['study_deck']:
            QMessageBox.information(self, 'Study', 'No cards to study.')
            return
        self.study_widget.start_session()
        self.stack.setCurrentWidget(self.study_widget)

    def scan_files(self):
        scan_files(self.data)
        QMessageBox.information(self, 'Scan', 'Files scanned.')

    def new_day(self):
        start_new_day(self.data, self.config)
        QMessageBox.information(
            self,
            'New Day',
            f"Study deck now has {len(self.data['study_deck'])} cards.",
        )


def gui_main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(500, 400)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    gui_main()
