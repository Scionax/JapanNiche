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

from .data import load_config, load_data, save_data
from .cards import scan_files, start_new_day, SCORE_MAP


class StudyWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cid = None
        self.card = None

        self.front_label = QLabel()
        self.front_label.setAlignment(Qt.AlignCenter)
        self.front_label.setFont(QFont('Arial', 20))

        self.orig_label = QLabel()
        self.desc_label = QLabel()
        self.pron_label = QLabel()
        self.jp_label = QLabel()
        self.jp_pron_label = QLabel()
        for lbl in (
            self.orig_label,
            self.desc_label,
            self.pron_label,
            self.jp_label,
            self.jp_pron_label,
        ):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont('Arial', 16))

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
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
        layout.addWidget(self.orig_label)
        layout.addWidget(self.desc_label)
        layout.addWidget(self.pron_label)
        layout.addWidget(self.jp_label)
        layout.addWidget(self.jp_pron_label)
        layout.addWidget(self.status_label)
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
        self.cid = random.choice(self.main_window.data['study_deck'])
        self.card = self.main_window.data['cards'][self.cid]
        self.front_label.setText(self.card['front'])
        for lbl in (
            self.orig_label,
            self.desc_label,
            self.pron_label,
            self.jp_label,
            self.jp_pron_label,
            self.status_label,
        ):
            lbl.setText('')
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
        jp = c.get('jp', c.get('front', ''))
        en = c.get('en', c.get('back', ''))
        pron = c.get('pron', '')
        hira = c.get('hira', '')
        self.orig_label.setText(jp)
        self.desc_label.setText(en)
        self.pron_label.setText(pron)
        self.jp_label.setText(hira)
        self.jp_pron_label.setText(pron.replace('-', ' '))
        self.status_label.setText(f"Score: {c['skill']}  Struggle: {c['struggle']}")
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
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def create_menu(self):
        widget = QWidget()
        layout = QVBoxLayout()
        toolbar = QHBoxLayout()

        def tool(text, icon, slot):
            btn = QToolButton()
            btn.setText(text)
            btn.setIcon(self.style().standardIcon(icon))
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)
            return btn

        tool('Study', QStyle.SP_ArrowForward, self.start_study)
        tool('Scan', QStyle.SP_BrowserReload, self.scan_files)
        tool('New Day', QStyle.SP_FileDialogNewFolder, self.new_day)
        tool('Quit', QStyle.SP_DialogCloseButton, self.close)

        layout.addLayout(toolbar)
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

    def new_day(self):
        start_new_day(self.data, self.config)
        QMessageBox.information(
            self,
            'New Day',
            f"Study deck now has {len(self.data['study_deck'])} cards.",
        )

