import sys

from PySide6.QtWidgets import QApplication
from blastimation.app import App


def print_usage():
    print("Usage:")
    print(f"{sys.argv[0]} <rom>")


def main():
    if len(sys.argv) != 2:
        print_usage()
        return

    print(f"Opening {sys.argv[1]}...")

    app = QApplication(sys.argv)
    widget = App()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
