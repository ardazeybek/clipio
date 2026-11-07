"""The running Clipio app: watches the clipboard, shows the panel, answers `clipio` commands."""
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCursor, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import APP_ID, __version__, ipc, system
from . import bridge
from .core import actions, config, db, export, ingest, maintenance, paths
from .system import active_app, autostart, hyprland
from .system.hotkey import GlobalHotkey
from .system.paste import Paster

UI_DIR = Path(__file__).resolve().parent / "ui"
LOGO = UI_DIR / "assets" / "clipio.svg"
MAINTENANCE_MS = 3600 * 1000      # hourly housekeeping
OWN_WRITE_GRACE = 1.0             # seconds to ignore clipboard events caused by Clipio itself
FOCUS_GRACE = 0.4                 # seconds after opening during which focus loss is ignored
CLOSE_ANIM_MS = 160               # time the panel needs for its close animation


class Controller:
    """Connects storage, clipboard backend, panel window, hotkey, tray and IPC."""

    def __init__(self, app: QApplication, clipboard, headless: bool = False):
        self.app = app
        self.clipboard = clipboard
        self.con = db.connect()
        self.paster = Paster()
        self.bridge = bridge.shared()   # must exist before any QML engine
        self.bridge.attach(self)
        self.window = None
        self.engine = None
        self.tray = None
        self.hotkey = None
        self._own_write = 0.0
        self._shown_at = 0.0
        self._headless = headless
        clipboard.changed.connect(self.on_clipboard_changed)

    # ---- startup ----

    # Load the QML panel; return False when it failed to load
    def load_ui(self) -> bool:
        self.engine = QQmlApplicationEngine()
        self.engine.load(str(UI_DIR / "Main.qml"))
        roots = self.engine.rootObjects()
        if not roots:
            return False
        self.window = roots[0]
        return True

    # Start the global shortcut; return True when it is active
    def start_hotkey(self, spec: str) -> bool:
        self.hotkey = GlobalHotkey()
        self.hotkey.activated.connect(self.toggle)
        return self.hotkey.start(spec)

    # Add the tray icon with its menu (skipped when the desktop has no tray)
    def start_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(QIcon(str(LOGO)), self.app)
        self.tray.setToolTip("Clipio")
        menu = QMenu()
        menu.addAction("Open Clipio", self.show)
        self._pause_action = menu.addAction("Pause recording")
        self._pause_action.setCheckable(True)
        self._pause_action.toggled.connect(self.set_paused)
        self._login_action = menu.addAction("Start at login")
        self._login_action.setCheckable(True)
        self._login_action.setChecked(autostart.is_enabled())
        self._login_action.toggled.connect(autostart.set_enabled)
        menu.addSeparator()
        menu.addAction("Quit Clipio", self.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self.toggle() if reason == QSystemTrayIcon.Trigger else None)
        self._menu = menu
        self.tray.show()

    # ---- state ----

    # Send the latest state to the panel and the tray menu
    def refresh(self) -> None:
        state = export.build_state(self.con)
        self.bridge.set_state(state)
        if self.tray:
            self._pause_action.blockSignals(True)
            self._pause_action.setChecked(state["paused"])
            self._pause_action.blockSignals(False)

    # Save what is on the clipboard now (or restore the last item if the clipboard was emptied)
    def on_clipboard_changed(self) -> None:
        if time.monotonic() - self._own_write < OWN_WRITE_GRACE:
            return
        cfg = config.load()
        snap = self.clipboard.read()
        if snap.is_empty():
            last = db.latest(self.con)
            if cfg["persist"] and last:
                self._own_write = time.monotonic()
                actions.copy(self.con, self.clipboard, last["id"])
            return
        if ingest.capture(self.con, snap, active_app.name(), cfg) is not None:
            maintenance.run(self.con, cfg)
            self.refresh()

    # ---- window ----

    # Place the window in the middle of the screen under the mouse pointer
    def _center_window(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.window.setX(area.x() + (area.width() - self.window.width()) // 2)
        self.window.setY(area.y() + (area.height() - self.window.height()) // 2)

    # Open the panel
    def show(self) -> None:
        if self.window is None:
            return
        self.paster.remember()
        self.refresh()
        self._shown_at = time.monotonic()
        self._center_window()
        self.window.show()
        self.window.raise_()
        self.window.requestActivate()
        if sys.platform == "darwin":
            from .system import macos
            macos.activate()
        self.bridge.set_shown(True)

    # Close the panel after its close animation
    def hide(self) -> None:
        if not self.bridge.shown:
            return
        self.bridge.set_shown(False)
        QTimer.singleShot(CLOSE_ANIM_MS, self._hide_window)

    # Hide the window itself (and on macOS give focus back to the previous app)
    def _hide_window(self) -> None:
        if self.window is not None and not self.bridge.shown:
            self.window.hide()
            if sys.platform == "darwin":
                from .system import macos
                macos.hide()

    # Open or close the panel
    def toggle(self) -> None:
        self.hide() if self.bridge.shown else self.show()

    # Close when the user clicks somewhere else (ignore the focus flicker right after opening)
    def focus_lost(self) -> None:
        if time.monotonic() - self._shown_at > FOCUS_GRACE:
            self.hide()

    # ---- item actions ----

    # Copy an item to the clipboard and, when asked, paste it into the previous app
    def activate(self, item_id: int, paste: bool) -> None:
        self._own_write = time.monotonic()
        if not actions.copy(self.con, self.clipboard, item_id):
            return
        self.refresh()
        self.bridge.set_shown(False)
        self._hide_window()
        if paste and self.paster.available():
            QTimer.singleShot(120, self.paster.paste)

    # Pin or unpin an item
    def toggle_pin(self, item_id: int) -> None:
        actions.toggle_pin(self.con, item_id)
        self.refresh()

    # Delete an item
    def delete(self, item_id: int) -> None:
        actions.delete(self.con, item_id)
        self.refresh()

    # Delete every unpinned item
    def clear(self) -> None:
        actions.clear(self.con)
        self.refresh()

    # Pause or resume recording
    def set_paused(self, paused: bool) -> None:
        actions.set_paused(bool(paused))
        self.refresh()

    # Change the retention period
    def set_retention(self, days: int) -> None:
        actions.set_retention(self.con, days)
        self.refresh()

    # Run the retention rules and update the panel
    def housekeeping(self) -> None:
        maintenance.run(self.con)
        self.refresh()

    # ---- commands from `clipio` ----

    # Answer one IPC command and return the reply text
    def handle_command(self, line: str) -> str:
        cmd, _, arg = line.partition(" ")
        simple = {"show": self.show, "hide": self.hide, "toggle": self.toggle,
                  "refresh": self.refresh, "quit": self.quit}
        if cmd == "ping":
            return "pong"
        if cmd in simple:
            QTimer.singleShot(0, simple[cmd])
            return "ok"
        if cmd in ("paste", "copy") and arg.strip().isdigit():
            QTimer.singleShot(0, lambda: self.activate(int(arg), cmd == "paste"))
            return "ok"
        return "unknown command"

    # Stop everything and leave the event loop
    def quit(self) -> None:
        if self.hotkey:
            self.hotkey.stop()
        self.clipboard.stop()
        if self.tray:
            self.tray.hide()
        self.app.quit()


# Create the Qt application with Clipio's name and icon
def create_application(argv: list[str]) -> QApplication:
    system.prepare_qt_env()
    app = QApplication.instance() or QApplication(argv)
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName("Clipio")
    app.setApplicationVersion(__version__)
    app.setDesktopFileName(APP_ID)
    app.setWindowIcon(QIcon(str(LOGO)))
    app.setQuitOnLastWindowClosed(False)
    return app


# Run Clipio until it is told to quit; return the exit code
def run(argv: list[str] | None = None) -> int:
    if ipc.is_running():
        print("Clipio is already running.")
        return 0
    app = create_application(argv or sys.argv[:1])
    if sys.platform == "darwin":
        from .system import macos
        macos.hide_dock_icon()
    paths.ensure_dirs()
    config.write_default_if_missing()
    cfg = config.load()

    hyprland.apply_window_rule()
    ctl = Controller(app, system.create_clipboard(app))
    maintenance.run(ctl.con, cfg)
    db.sweep_orphan_images(ctl.con)
    if not ctl.load_ui():
        print("clipio: the panel could not be loaded.", file=sys.stderr)
        return 1

    server = ipc.Server(ctl.handle_command)
    if not server.listen():
        print("clipio: could not open the command channel.", file=sys.stderr)
    if not ctl.start_hotkey(cfg["hotkey"]):
        print("clipio: no global shortcut on this desktop; bind `clipio toggle` "
              "in your desktop's keyboard settings.", file=sys.stderr)
    ctl.start_tray()
    ctl.refresh()

    timer = QTimer()
    timer.timeout.connect(ctl.housekeeping)
    timer.start(MAINTENANCE_MS)
    code = app.exec()
    server.close()
    return code
