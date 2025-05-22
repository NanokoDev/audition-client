import sys
from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QApplication

from app.controllers.main_controller import MainController


def main():
    """Main entry point of the application"""
    QDir.addSearchPath("resources", "app/resources")

    app = QApplication(sys.argv)
    app.setApplicationName("Audition Admin")

    controller = MainController()
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
