import sys
from PySide6.QtWidgets import QApplication
from ui.ui_main_workspace_window import MainWindow


def main():
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()