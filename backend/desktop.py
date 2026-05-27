"""TempTeller native desktop app: a Qt window + system-tray icon, serving the dashboard.

Closing the window hides it to the tray (left-click the tray icon to toggle,
right-click for a menu). The FastAPI server runs in a background thread.
"""
import sys
import threading
import time
import urllib.request
from pathlib import Path

import uvicorn
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView

from server import app

HOST, PORT = "127.0.0.1", 8000
URL = f"http://{HOST}:{PORT}"
ICON = Path(__file__).parent.parent / "assets" / "icon.png"


def serve():
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def wait_ready(timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(URL, timeout=1)
            return
        except Exception:
            time.sleep(0.2)


class MainWindow(QMainWindow):
    def __init__(self, icon):
        super().__init__()
        self.setWindowTitle("TempTeller")
        self.setWindowIcon(icon)
        self.resize(960, 760)
        self.setMinimumSize(280, 220)
        self.view = QWebEngineView()
        self.view.load(QUrl(URL))
        self.setCentralWidget(self.view)
        self._quitting = False

    def closeEvent(self, event):
        # Hide to tray instead of quitting, unless quit was chosen explicitly.
        if self._quitting:
            event.accept()
        else:
            event.ignore()
            self.hide()


def main():
    threading.Thread(target=serve, daemon=True).start()
    wait_ready()

    qt = QApplication(sys.argv)
    qt.setApplicationName("TempTeller")
    qt.setDesktopFileName("TempTeller")
    qt.setQuitOnLastWindowClosed(False)  # closing the window keeps us in the tray

    # Prefer the themed icon (sent to the tray by *name*, which Mint's xapp
    # applet renders reliably); fall back to the raw file.
    icon = QIcon.fromTheme("tempteller")
    if icon.isNull() and ICON.exists():
        icon = QIcon(str(ICON))

    win = MainWindow(icon)
    if "--tray" not in sys.argv:  # autostart passes --tray to start hidden
        win.show()

    def toggle():
        if win.isVisible():
            win.hide()
        else:
            win.showNormal()
            win.raise_()
            win.activateWindow()

    tray = QSystemTrayIcon(icon)
    tray.setToolTip("TempTeller")
    menu = QMenu()
    menu.addAction("Show / Hide", toggle)
    menu.addSeparator()

    def quit_app():
        win._quitting = True
        qt.quit()

    menu.addAction("Quit", quit_app)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: toggle() if reason == QSystemTrayIcon.Trigger else None
    )
    tray.show()

    sys.exit(qt.exec_())


if __name__ == "__main__":
    main()
