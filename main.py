from japan_niche.gui import MainWindow
from PyQt5.QtWidgets import QApplication
import sys


def gui_main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    gui_main()
