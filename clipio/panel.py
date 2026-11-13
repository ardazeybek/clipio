"""The Clipio panel process: loads the QML window, shows items and quits by itself when unused.

The background service (`clipio/app.py`) starts it with `python -m clipio panel` when the panel
opens. It reads and changes the database itself, but anything that touches the clipboard or the
paste keystroke goes to the service. After `panel_keep_minutes` closed it quits, so the memory
of QML, the graphics driver and fonts goes back to the system.
"""
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from . import bridge, ipc, system
from .core import actions, config, db, export, paths
from .system import hyprland, ocr

UI_DIR = Path(__file__).resolve().parent / "ui"
FOCUS_GRACE = 0.4                 # seconds after opening during which focus loss is ignored
REFOCUS_GRACE = 2.0               # Hyprland: focus stolen this soon without the mouse moving is taken back
FOCUS_RETRY_MS = (40, 250)        # Hyprland: ask for focus again this long after showing
CLOSE_ANIM_MS = 160               # time the panel needs for its close animation


# Send a command to the background service and return its reply ('' when it does not answer)
def to_service(command: str) -> str:
    return ipc.send(command) or ""


class PanelController:
    """Runs the panel window; `service(command) -> reply` reaches the background service."""

    def __init__(self, app, service=to_service):
        self.app = app
        self.service = service
        self.con = db.connect()
        self.bridge = bridge.shared()   # must exist before any QML engine
        self.bridge.attach(self)
        self.window = None
        self.engine = None
        self._open_cursor = None
        self._shown_at = 0.0
        self.queue: list[int] = []      # last known paste queue (owned by the service)
        self._idle = QTimer()
        self._idle.setSingleShot(True)
        self._idle.timeout.connect(self._idle_quit)

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

    # ---- state ----

    # Send the latest state (with the service's paste queue) to the panel
    def refresh(self) -> None:
        state = export.build_state(self.con, ocr_available=ocr.available())
        reply = self.service("queue?")
        self.queue = [int(i) for i in reply.split() if i.isdigit()]
        state["queue"] = list(self.queue)
        self.bridge.set_state(state)

    # A background job finished (runs in the main thread)
    def worker_done(self, kind: str, item_id: int, text: str) -> None:
        if kind == "ocr":
            new_id = actions.save_text(self.con, text, "OCR") if text else None
            if new_id is None:
                self.bridge.notice.emit("noText")
            else:
                self.refresh()
                self.bridge.created.emit(new_id)
                return
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
        self._idle.stop()
        self.refresh()
        self._shown_at = time.monotonic()
        self._center_window()
        # Hyprland drops runtime rules on config reload, so add the panel rule again before mapping
        hyprland.apply_window_rule()
        self.window.show()
        self.window.raise_()
        self.window.requestActivate()
        if sys.platform == "darwin":
            from .system import macos
            macos.activate()
        elif sys.platform == "win32":
            from .system import windows
            windows.force_focus(int(self.window.winId()))
        self.bridge.set_shown(True)
        self.service("panel shown")
        self._claim_focus()

    # Hyprland: take keyboard focus and note where the mouse was when the panel opened
    def _claim_focus(self) -> None:
        if not system.is_hyprland():
            return
        self._open_cursor = hyprland.cursor_pos()
        for ms in FOCUS_RETRY_MS:
            QTimer.singleShot(ms, lambda: self.bridge.shown and hyprland.focus_panel())

    # Close the panel after its close animation
    def hide(self) -> None:
        if not self.bridge.shown:
            return
        self.bridge.set_shown(False)
        QTimer.singleShot(CLOSE_ANIM_MS, self._hide_window)

    # Hide the window itself, tell the service and start the countdown to quitting
    def _hide_window(self) -> None:
        if self.window is None or self.bridge.shown:
            return
        self.window.hide()
        if sys.platform == "darwin":
            from .system import macos
            macos.hide()   # gives focus back to the previous app
        self.service("panel hidden")
        self._idle.start(max(config.load()["panel_keep_minutes"] * 60_000, CLOSE_ANIM_MS))

    # Open or close the panel
    def toggle(self) -> None:
        self.hide() if self.bridge.shown else self.show()

    # Close when the user clicks somewhere else (ignore the focus flicker right after opening)
    def focus_lost(self) -> None:
        age = time.monotonic() - self._shown_at
        if age <= FOCUS_GRACE:
            return
        # Hyprland hands focus to the window under the mouse once the panel settles; that is not a click elsewhere
        if system.is_hyprland() and age <= REFOCUS_GRACE and self._open_cursor is not None \
                and hyprland.cursor_pos() == self._open_cursor:
            hyprland.focus_panel()
            return
        self.hide()

    # Unused long enough: quit so the memory goes back to the system
    def _idle_quit(self) -> None:
        if not self.bridge.shown:
            self.quit()

    # ---- item actions ----

    # Have the service copy (and paste) an item; the panel closes when that worked
    def activate(self, item_id: int, paste: bool, clean_it: bool = False) -> None:
        reply = self.service(f"activate {item_id} {int(paste)} {int(clean_it)}")
        if reply != "ok":
            self.refresh()   # a broken item may have been removed
            return
        self.bridge.set_shown(False)
        self._hide_window()

    # Paste the given items one after another (the service keeps the queue)
    def start_queue(self, ids: list[int]) -> None:
        self.bridge.set_shown(False)
        self._hide_window()
        self.service("queue " + " ".join(str(i) for i in ids))

    # Paste the next queued item
    def paste_next(self) -> None:
        self.bridge.set_shown(False)
        self._hide_window()
        self.service("next")

    # Forget the paste queue
    def clear_queue(self) -> None:
        self.service("clearqueue")
        self.refresh()

    # Save edited text and paste (or only copy) it
    def paste_edited(self, text: str, paste: bool) -> None:
        item_id = actions.save_text(self.con, text)
        if item_id is not None:
            self.activate(item_id, paste)

    # Whole text of an item ('' for images or missing items)
    def full_text(self, item_id: int) -> str:
        row = db.get(self.con, item_id)
        return (row["text"] or "") if row else ""

    # Conversions that work on an item
    def conversions(self, item_id: int) -> list[str]:
        return actions.conversions(self.con, item_id)

    # Convert an item into a new one and select it in the panel
    def convert(self, item_id: int, name: str) -> None:
        new_id = actions.convert(self.con, item_id, name)
        self.refresh()
        if new_id is not None:
            self.bridge.created.emit(new_id)

    # Read an image's text in the background
    def ocr(self, item_id: int) -> None:
        row = db.get(self.con, item_id)
        if not row or row["kind"] != "image":
            return
        image = paths.image_dir() / row["image_file"]
        threading.Thread(target=lambda: self.bridge.post("ocr", item_id, ocr.read_text(image)),
                         daemon=True).start()

    # Put an item in a folder
    def set_tag(self, item_id: int, tag: str) -> None:
        actions.set_tag(self.con, item_id, tag)
        self.refresh()

    # Stop or start saving copies from an app
    def set_app_ignored(self, app: str, ignored: bool) -> None:
        (actions.ignore_app if ignored else actions.unignore_app)(app)
        self.refresh()

    # Turn an on/off setting on or off
    def set_switch(self, key: str, on: bool) -> None:
        actions.set_switch(key, on)
        self.refresh()

    # Change one panel shortcut
    def set_shortcut(self, action: str, keys: str) -> None:
        actions.set_shortcut(action, keys)
        self.refresh()

    # Put every panel shortcut back to its default
    def reset_shortcuts(self) -> None:
        actions.reset_shortcuts()
        self.refresh()

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

    # Change how long the closed panel stays loaded
    def set_panel_keep(self, minutes: int) -> None:
        actions.set_panel_keep(minutes)
        self.refresh()

    # ---- commands from the service ----

    # Answer one IPC command from the service
    def handle_command(self, line: str) -> str:
        actions_ = {"show": self.show, "hide": self.hide, "toggle": self.toggle,
                    "refresh": self.refresh, "quit": self.quit}
        if line == "ping":
            return "pong"
        if line in actions_:
            QTimer.singleShot(0, actions_[line])
            return "ok"
        return "unknown command"

    # Tell the service the panel is gone and leave the event loop
    def quit(self) -> None:
        self._idle.stop()
        if self.window is not None:
            self.window.hide()
        self.service("panel exit")
        self.app.quit()


# Run the panel process: open the panel at once, quit when unused; return the exit code
def run(argv: list[str] | None = None) -> int:
    from .app import create_application
    paths.ensure_dirs()
    lock = QLockFile(str(paths.data_dir() / "panel.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        # a panel already runs (e.g. left over from an earlier service): open that one
        return 0 if ipc.send("show", 2000, ipc.PANEL) == "ok" else 1
    app = create_application(argv or sys.argv[:1], QGuiApplication)
    if sys.platform == "darwin":
        from .system import macos
        macos.hide_dock_icon()
    ctl = PanelController(app)
    if not ctl.load_ui():
        print("clipio: the panel could not be loaded.", file=sys.stderr)
        ctl.service("panel exit")
        return 1
    server = ipc.Server(ctl.handle_command, role=ipc.PANEL)
    if not server.listen():
        print("clipio: could not open the panel channel.", file=sys.stderr)
    ctl.service("panel ready")
    QTimer.singleShot(0, ctl.show)
    code = app.exec()
    server.close()
    lock.unlock()
    return code
