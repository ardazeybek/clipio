"""The Clipio background service: watches the clipboard, pastes, owns the hotkey, tray and `clipio` commands.

It stays small on purpose (no QML, no graphics driver): the panel runs in its own process
(`clipio/panel.py`), started on demand by `PanelLink` and closed again after a while unused.
"""
import sys
import time
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import APP_ID, __version__, ipc, system
from .core import actions, config, db, ingest, maintenance, paths
from .panel_link import PanelLink
from .system import active_app, autostart, linktitle, memory
from .system.hotkey import GlobalHotkey
from .system.paste import Paster

UI_DIR = Path(__file__).resolve().parent / "ui"
LOGO = UI_DIR / "assets" / "clipio.svg"
MAINTENANCE_MS = 3600 * 1000      # hourly housekeeping
OWN_WRITE_GRACE = 1.0             # seconds to ignore clipboard events caused by Clipio itself
PASTE_DELAY_MS = 120              # time the panel needs to give focus back before the paste keystroke
QUEUE_PRELOAD_MS = 600            # copy the next queued item this long after a queued paste
BIG_ITEM = 512 * 1024             # after saving something this big, give memory back to the OS


class _Relay(QObject):
    """Moves a background thread's result to the main thread."""
    done = Signal(int, str)


class Controller:
    """Connects storage, clipboard backend, paste keystroke, panel process, hotkey, tray and IPC."""

    def __init__(self, app: QApplication, clipboard, panel: PanelLink | None = None):
        self.app = app
        self.clipboard = clipboard
        self.con = db.connect()
        self.paster = Paster()
        self.panel = panel or PanelLink(before_show=self.paster.remember)
        self.tray = None
        self.hotkey = None
        self.queue: list[int] = []       # items still to paste with `clipio next`
        self._own_write = 0.0
        self._relay = _Relay()
        self._relay.done.connect(self._title_found)
        clipboard.changed.connect(self.on_clipboard_changed)

    # ---- startup ----

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
        self._login_action.toggled.connect(autostart.set_enabled)
        menu.addSeparator()
        menu.addAction("Quit Clipio", self.quit)
        menu.aboutToShow.connect(self._sync_tray)   # the panel may have changed these meanwhile
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self.toggle() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self._menu = menu
        self._sync_tray()
        self.tray.show()

    # Show the current pause and autostart state in the tray menu
    def _sync_tray(self) -> None:
        if not self.tray:
            return
        for action, on in ((self._pause_action, paths.pause_file().exists()),
                           (self._login_action, autostart.is_enabled())):
            action.blockSignals(True)
            action.setChecked(on)
            action.blockSignals(False)

    # ---- state ----

    # Tell an open panel and the tray that something changed
    def refresh(self) -> None:
        self.panel.refresh()
        self._sync_tray()

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
        item_id = ingest.capture(self.con, snap, active_app.name(), cfg)
        big = len(snap.image or b"") + len(snap.text or b"") > BIG_ITEM
        del snap
        if item_id is not None:
            maintenance.run(self.con, cfg)
            self._maybe_fetch_title(item_id, cfg)
            self.refresh()
        if big:
            memory.trim()

    # Look up a copied link's page title in the background (when link_titles is on)
    def _maybe_fetch_title(self, item_id: int, cfg: dict) -> None:
        row = db.get(self.con, item_id)
        if cfg["link_titles"] and row and row["hint"] == "url" and not row["title"] and not row["secret"]:
            linktitle.fetch_async(row["text"].strip(), lambda t: self._relay.done.emit(item_id, t))

    # A page title arrived (main thread)
    def _title_found(self, item_id: int, title: str) -> None:
        db.set_title(self.con, item_id, title)
        self.refresh()

    # ---- panel ----

    # Open the panel
    def show(self) -> None:
        self.panel.show()

    # Close the panel
    def hide(self) -> None:
        self.panel.hide()

    # Open or close the panel
    def toggle(self) -> None:
        self.panel.toggle()

    # ---- clipboard actions ----

    # Copy an item to the clipboard and, when asked, paste it into the previous app
    def activate(self, item_id: int, paste: bool, clean_it: bool = False) -> bool:
        self._own_write = time.monotonic()
        if not actions.copy(self.con, self.clipboard, item_id, clean_it):
            return False
        if self.panel.shown:   # e.g. `clipio paste <id>` while the panel is open
            self.panel.hide()
        if paste and self.paster.available():
            QTimer.singleShot(PASTE_DELAY_MS, self.paster.paste)
        return True

    # Paste the first item now and keep the rest for `clipio next`
    def start_queue(self, ids: list[int]) -> None:
        self.queue = [i for i in ids if db.get(self.con, i)]
        self.paste_next()

    # Paste the next queued item (the queue ends when it is empty)
    def paste_next(self) -> None:
        if not self.queue:
            return
        self.activate(self.queue.pop(0), True)
        if self.queue:   # put the next one on the clipboard, so a plain Ctrl+V also gives it
            QTimer.singleShot(QUEUE_PRELOAD_MS, self._preload_next)

    # Copy the next queued item after the current paste went through
    def _preload_next(self) -> None:
        if self.queue:
            self._own_write = time.monotonic()
            actions.copy(self.con, self.clipboard, self.queue[0])

    # Forget the paste queue
    def clear_queue(self) -> None:
        self.queue = []

    # Pause or resume recording
    def set_paused(self, paused: bool) -> None:
        actions.set_paused(bool(paused))
        self.refresh()

    # Run the retention rules, tell the panel and give memory back
    def housekeeping(self) -> None:
        maintenance.run(self.con)
        self.refresh()
        memory.trim()

    # ---- commands from `clipio` and the panel ----

    # Answer one IPC command and return the reply text
    def handle_command(self, line: str) -> str:
        cmd, _, arg = line.partition(" ")
        args = arg.split()
        simple = {"show": self.show, "hide": self.hide, "toggle": self.toggle,
                  "refresh": self.refresh, "quit": self.quit, "next": self.paste_next}
        if cmd == "ping":
            return "pong"
        if cmd in simple:
            QTimer.singleShot(0, simple[cmd])
            return "ok"
        if cmd in ("paste", "copy") and arg.strip().isdigit():
            QTimer.singleShot(0, lambda: self.activate(int(arg), cmd == "paste"))
            return "ok"
        if cmd == "activate" and len(args) == 3 and all(a.isdigit() for a in args):
            # from the panel: answered right away, so the panel knows whether to close
            return "ok" if self.activate(int(args[0]), args[1] == "1", args[2] == "1") else "failed"
        if cmd == "queue":
            ids = [int(i) for i in args if i.isdigit()]
            QTimer.singleShot(0, lambda: self.start_queue(ids))
            return "ok"
        if cmd == "queue?":
            return " ".join(map(str, self.queue))
        if cmd == "clearqueue":
            self.clear_queue()
            return "ok"
        if cmd == "panel":
            return self.panel.report(arg.strip())
        return "unknown command"

    # Stop everything (the panel too) and leave the event loop
    def quit(self) -> None:
        self.panel.quit()
        if self.hotkey:
            self.hotkey.stop()
        self.clipboard.stop()
        if self.tray:
            self.tray.hide()
        self.app.quit()


# Create the Qt application with Clipio's name and icon (also used by the panel process)
def create_application(argv: list[str], cls=QApplication):
    system.prepare_qt_env()
    app = cls.instance() or cls(argv)
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName("Clipio")
    app.setApplicationVersion(__version__)
    app.setDesktopFileName(APP_ID)
    app.setWindowIcon(QIcon(str(LOGO)))
    app.setQuitOnLastWindowClosed(False)
    return app


# Run the Clipio service until it is told to quit; return the exit code
def run(argv: list[str] | None = None) -> int:
    # one Clipio per user: a lock file (freed by the OS if Clipio crashes) guards startup,
    # so two quick `clipio toggle` presses cannot start two copies
    paths.ensure_dirs()
    lock = QLockFile(str(paths.lock_file()))
    lock.setStaleLockTime(0)
    if ipc.is_running() or not lock.tryLock(0):
        print("Clipio is already running.")
        return 0
    app = create_application(argv or sys.argv[:1])
    if sys.platform == "darwin":
        from .system import macos
        macos.hide_dock_icon()
    config.write_default_if_missing()
    cfg = config.load()

    ctl = Controller(app, system.create_clipboard(app))
    maintenance.run(ctl.con, cfg)
    db.sweep_orphan_images(ctl.con)

    server = ipc.Server(ctl.handle_command)
    if not server.listen():
        print("clipio: could not open the command channel.", file=sys.stderr)
    if not ctl.start_hotkey(cfg["hotkey"]):
        print("clipio: no global shortcut on this desktop; bind `clipio toggle` "
              "in your desktop's keyboard settings.", file=sys.stderr)
    ctl.start_tray()

    timer = QTimer()
    timer.timeout.connect(ctl.housekeeping)
    timer.start(MAINTENANCE_MS)
    QTimer.singleShot(3000, memory.trim)   # drop what startup needed
    code = app.exec()
    server.close()
    lock.unlock()
    return code
