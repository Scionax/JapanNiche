import random
import datetime
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QStackedWidget,
    QToolButton,
    QStyle,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# Mapping of hiragana characters to their romanized pronunciations used for
# displaying per-character readings on the reveal card.
HIRAGANA_PRONUNCIATIONS = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo',
    'っ': 'tsu', 'ゎ': 'wa',
    'ー': '-',
}

from .data import load_config, load_data, save_data
from .cards import scan_files, start_new_day, SCORE_MAP


class StudyWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cid = None
        self.card = None
        self.direction = 'J2E'

        self.front_label = QLabel()
        self.front_label.setAlignment(Qt.AlignCenter)
        self.front_label.setFont(QFont('Arial', 24))

        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.pron_label = QLabel()
        self.jp_label = QLabel()
        for lbl in (
            self.desc_label,
            self.pron_label,
            self.jp_label,
        ):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont('Arial', 16))

        self.desc_label.setFont(QFont('Arial', 18))
        self.pron_label.setFont(QFont('Arial', 16))
        self.jp_label.setFont(QFont('Arial', 16))

        # Container used to display hiragana characters with their romanized
        # readings underneath each character when revealing a card.
        self.hira_layout = QHBoxLayout()
        self.hira_layout.setAlignment(Qt.AlignCenter)
        self.hira_layout.setSpacing(8)
        self.hira_container = QWidget()
        self.hira_container.setLayout(self.hira_layout)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignRight)
        self.status_label.setFont(QFont('Arial', 12))

        self.show_btn = QPushButton('Show Answer')

        rating_layout = QHBoxLayout()
        self.btn_wrong = QPushButton('Wrong (A)')
        self.btn_unsure = QPushButton('Unsure (S)')
        self.btn_correct = QPushButton('Correct (D)')
        self.btn_easy = QPushButton('Easy (F)')
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
        layout.addSpacing(16)
        layout.addWidget(self.desc_label)
        layout.addSpacing(16)
        layout.addWidget(self.pron_label)
        layout.addSpacing(16)
        layout.addWidget(self.jp_label)
        layout.addWidget(self.hira_container)
        layout.addStretch()
        layout.addWidget(self.show_btn)
        layout.addLayout(rating_layout)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.setFocusPolicy(Qt.StrongFocus)

        self.show_btn.clicked.connect(self.show_answer)
        self.btn_wrong.clicked.connect(lambda: self.rate('A'))
        self.btn_unsure.clicked.connect(lambda: self.rate('S'))
        self.btn_correct.clicked.connect(lambda: self.rate('D'))
        self.btn_easy.clicked.connect(lambda: self.rate('F'))

    def _clear_hira_layout(self):
        """Remove all widgets from the hiragana display layout."""
        while self.hira_layout.count():
            item = self.hira_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def start_session(self):
        self.next_card()
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and self.show_btn.isEnabled():
            self.show_answer()
        elif event.key() == Qt.Key_A and self.btn_wrong.isEnabled():
            self.rate('A')
        elif event.key() == Qt.Key_S and self.btn_unsure.isEnabled():
            self.rate('S')
        elif event.key() == Qt.Key_D and self.btn_correct.isEnabled():
            self.rate('D')
        elif event.key() == Qt.Key_F and self.btn_easy.isEnabled():
            self.rate('F')
        else:
            super().keyPressEvent(event)

    def next_card(self):
        if not self.main_window.data['study_deck']:
            QMessageBox.information(self, 'Done', 'Study session complete!')
            self.main_window.show_menu()
            return
        while True:
            if not self.main_window.data['study_deck']:
                QMessageBox.information(self, 'Done', 'Study session complete!')
                self.main_window.show_menu()
                return

            self.cid = random.choice(self.main_window.data['study_deck'])
            self.card = self.main_window.data['cards'][self.cid]

            directions = [
                d for d in ('J2E', 'E2J') if self.card['skill'].get(d, 0) < 2
            ]

            if directions:
                self.direction = random.choice(directions)
                break

            # If no directions remain, the card is finished. Move to review and
            # continue selecting another card.
            self.card['deck'] = 'review'
            self.card['ratings'] = {'J2E': [], 'E2J': []}
            self.card['skill'] = {'J2E': 0, 'E2J': 0}
            self.card['struggle'] = {'J2E': 0, 'E2J': 0}
            self.main_window.data['study_deck'].remove(self.cid)
            save_data(self.main_window.data)
            self.main_window.update_counts()

        front = self.card['jp'] if self.direction == 'J2E' else self.card['en']
        self.front_label.setText(front)
        for lbl in (
            self.desc_label,
            self.pron_label,
            self.jp_label,
            self.status_label,
        ):
            lbl.setText('')
        self._clear_hira_layout()
        self.show_btn.setEnabled(True)
        for btn in (
            self.btn_wrong,
            self.btn_unsure,
            self.btn_correct,
            self.btn_easy,
        ):
            btn.setEnabled(False)

    def show_answer(self):
        c = self.card
        direction = self.direction
        jp = c.get('jp', '')
        en = c.get('en', '')
        pron = c.get('pron', '')
        hira = c.get('hira', '')

        if direction == 'E2J':
            answer = jp
            extra = ''
        else:
            answer = en
            extra = ''

        self.desc_label.setText(answer)
        self.pron_label.setText(f"[{pron}]")
        self.jp_label.setText(extra)
        self._clear_hira_layout()
        for char in hira:
            char_lbl = QLabel(char)
            char_lbl.setAlignment(Qt.AlignHCenter)
            char_lbl.setFont(QFont('Arial', 32))

            roman = HIRAGANA_PRONUNCIATIONS.get(char, char)
            roman_lbl = QLabel(roman)
            roman_lbl.setAlignment(Qt.AlignHCenter)
            roman_lbl.setFont(QFont('Arial', 14))
            roman_lbl.setStyleSheet('color: gray')

            vbox = QVBoxLayout()
            vbox.setSpacing(12)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.addWidget(char_lbl)
            vbox.addWidget(roman_lbl)

            w = QWidget()
            w.setLayout(vbox)
            self.hira_layout.addWidget(w)

        self.status_label.setText(
            f"Score: {c['skill'][direction]}  Struggle: {c['struggle'][direction]}"
        )
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
        dir_ = self.direction
        card['ratings'][dir_].append(rating)
        if len(card['ratings'][dir_]) > 3:
            card['ratings'][dir_].pop(0)
        card['skill'][dir_] = sum(SCORE_MAP[x] for x in card['ratings'][dir_])
        if rating == 'A':
            card['struggle'][dir_] += 3
        elif rating == 'S':
            card['struggle'][dir_] += 1
        card['last_study'][dir_] = datetime.datetime.now().timestamp()
        if card['skill']['J2E'] >= 2 and card['skill']['E2J'] >= 2:
            card['deck'] = 'review'
            card['ratings'] = {'J2E': [], 'E2J': []}
            card['skill'] = {'J2E': 0, 'E2J': 0}
            card['struggle'] = {'J2E': 0, 'E2J': 0}
            self.main_window.data['study_deck'].remove(self.cid)
        save_data(self.main_window.data)
        self.main_window.update_counts()
        self.next_card()


class MainWindow(QWidget):
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

        layout = QVBoxLayout()
        self.toolbar_layout = self.create_toolbar()
        layout.addLayout(self.toolbar_layout)
        layout.addWidget(self.stack)
        self.setLayout(layout)
        self.update_counts()

    def create_menu(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addStretch()
        widget.setLayout(layout)
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
        self.update_counts()

    def new_day(self):
        start_new_day(self.data, self.config)
        QMessageBox.information(
            self,
            'New Day',
            f"Study deck now has {len(self.data['study_deck'])} cards.",
        )
        self.update_counts()

    def create_toolbar(self):
        layout = QHBoxLayout()

        def tool(text, icon, slot):
            btn = QToolButton()
            btn.setText(text)
            btn.setIcon(self.style().standardIcon(icon))
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.clicked.connect(slot)
            layout.addWidget(btn)
            return btn

        tool('Study', QStyle.SP_ArrowForward, self.start_study)
        tool('Scan', QStyle.SP_BrowserReload, self.scan_files)
        tool('New Day', QStyle.SP_FileDialogNewFolder, self.new_day)
        tool('Quit', QStyle.SP_DialogCloseButton, self.close)

        layout.addStretch()
        self.lbl_study = QLabel()
        self.lbl_review = QLabel()
        self.lbl_no = QLabel()
        for lbl in (self.lbl_study, self.lbl_review, self.lbl_no):
            layout.addWidget(lbl)
        return layout

    def update_counts(self):
        counts = {'study': 0, 'review': 0, 'no_deck': 0}
        for card in self.data['cards'].values():
            deck = card.get('deck', 'no_deck')
            if deck in counts:
                counts[deck] += 1
        self.lbl_study.setText(f"Study: {counts['study']}")
        self.lbl_review.setText(f"Review: {counts['review']}")
        self.lbl_no.setText(f"No Deck: {counts['no_deck']}")

