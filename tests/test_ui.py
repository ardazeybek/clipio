"""Loads the real QML panel headless and drives it, failing on any QML warning."""
import struct
import zlib

import pytest
from PySide6.QtCore import QObject, QTimer, Signal, QtMsgType, qInstallMessageHandler

from clipio.core import db, ingest, config
from clipio.core.ingest import Snapshot

# Build a valid PNG in memory
def make_png(w=4, h=3) -> bytes:
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    raw = b"".join(b"\x00" + b"\xe5\x8f\x6f" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class StubClipboard(QObject):
    """Qt-shaped clipboard backend that keeps everything in memory."""
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.snap = Snapshot()

    # Return the stored snapshot
    def read(self):
        return self.snap

    # Store text as the clipboard content
    def write_text(self, text):
        self.snap = Snapshot(formats=["text/plain"], text=text.encode())
        return True

    # Store an image as the clipboard content
    def write_image(self, data, mime):
        self.snap = Snapshot(formats=[mime], image=data, image_mime=mime)
        return True

    # Nothing to stop
    def stop(self):
        pass


# Spin the Qt event loop for a while
def pump(app, ms):
    loop_done = []
    QTimer.singleShot(ms, lambda: loop_done.append(True))
    while not loop_done:
        app.processEvents()


# Fill the database with one item of every kind
def seed(con):
    cfg = config.load()
    samples = ["Meeting moved to Thursday", "https://example.com/page", "#E58F6F",
               "def hello():\n    print('hi')\n    return 1\n", "someone@example.com"]
    for s in samples:
        ingest.capture(con, Snapshot(formats=["text/plain"], text=s.encode()), "editor", cfg)
    ingest.capture(con, Snapshot(formats=["image/png"], image=make_png()), "viewer", cfg)


class StubPanelLink:
    """Service-side panel link that drives the in-process panel directly (no second process)."""

    def __init__(self):
        self.panel = None
        self.shown = False
        self.running = True

    def show(self):
        self.panel.show()

    def hide(self):
        self.panel.hide()

    def toggle(self):
        self.panel.toggle()

    def refresh(self):
        self.panel.refresh()

    def quit(self):
        pass

    def report(self, state):
        self.shown = state == "shown"
        return "ok"


@pytest.fixture(scope="session")
def ui(qapp, tmp_path_factory):
    """One service controller and one panel (one QML engine) for the whole session
    (Qt allows only one engine to use the Backend singleton)."""
    from clipio.app import Controller
    from clipio.panel import PanelController
    base = tmp_path_factory.mktemp("ui")
    mp = pytest.MonkeyPatch()
    mp.setenv("CLIPIO_DATA_DIR", str(base / "data"))
    mp.setenv("CLIPIO_CONFIG_DIR", str(base / "config"))
    warnings = []

    # Collect every QML warning or error (not notes from the headless test platform itself)
    def handler(mode, ctx, msg):
        if "plugin does not support" in msg:
            return
        if mode in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            warnings.append(msg)

    previous = qInstallMessageHandler(handler)
    link = StubPanelLink()
    svc = Controller(qapp, StubClipboard(), panel=link)
    panel = PanelController(qapp, service=svc.handle_command)
    panel.quit = lambda: None          # the test app must keep running
    link.panel = panel
    assert panel.load_ui(), warnings
    yield svc, panel, warnings, base
    panel.window.hide()
    qInstallMessageHandler(previous)
    mp.undo()


@pytest.fixture
def controller(ui, monkeypatch):
    svc, panel, warnings, base = ui
    # use the session folders the controller's database lives in, not the per-test ones
    monkeypatch.setenv("CLIPIO_DATA_DIR", str(base / "data"))
    monkeypatch.setenv("CLIPIO_CONFIG_DIR", str(base / "config"))
    svc.con.execute("DELETE FROM items")
    svc.con.commit()
    seed(svc.con)
    svc.queue = []
    panel.refresh()
    warnings.clear()
    yield svc, panel, warnings
    panel.hide()


def test_panel_loads_and_lists_items(qapp, controller):
    svc, panel, warnings = controller
    svc.show()
    pump(qapp, 700)
    assert panel.window.isVisible()
    assert panel.bridge.shown
    assert svc.panel.shown            # the panel told the service it is open
    assert len(__import__("json").loads(panel.bridge.stateJson)["items"]) == 6
    assert not warnings, warnings


def test_new_clipboard_content_is_saved(qapp, controller):
    svc, panel, warnings = controller
    svc.clipboard.snap = Snapshot(formats=["text/plain"], text=b"fresh copy")
    svc.on_clipboard_changed()
    rows = db.list_items(svc.con)
    assert any(r["text"] == "fresh copy" for r in rows)
    assert "fresh copy" in panel.bridge.stateJson   # the open panel was refreshed
    assert not warnings, warnings


def test_actions_from_the_panel(qapp, controller):
    svc, panel, warnings = controller
    svc.show()
    pump(qapp, 300)
    first = db.list_items(svc.con)[0]["id"]
    panel.bridge.togglePin(first)
    assert db.get(svc.con, first)["pinned"] == 1
    panel.bridge.setRetention(7)
    assert config.load()["retention_days"] == 7
    panel.bridge.setPaused(True)
    panel.bridge.setPaused(False)
    panel.bridge.activate(first, False)        # copy only: goes through the service
    pump(qapp, 300)
    assert not svc.clipboard.snap.is_empty()
    assert not panel.bridge.shown
    assert not svc.panel.shown
    panel.bridge.clearAll()
    assert all(r["pinned"] for r in db.list_items(svc.con))
    pump(qapp, 300)
    assert not warnings, warnings


def test_paste_queue_lives_in_the_service(qapp, controller):
    svc, panel, warnings = controller
    ids = [r["id"] for r in db.list_items(svc.con)][:3]
    svc.show()
    pump(qapp, 300)
    panel.bridge.startQueue(ids)
    pump(qapp, 100)
    assert svc.queue == ids[1:]
    panel.refresh()
    assert panel.queue == ids[1:]
    panel.bridge.clearQueue()
    assert svc.queue == [] and panel.queue == []
    assert not warnings, warnings


def test_panel_quits_after_idle(qapp, controller, monkeypatch):
    svc, panel, warnings = controller
    quits = []
    monkeypatch.setattr(panel, "quit", lambda: quits.append(1))
    config.set_int("panel_keep_minutes", 0)
    svc.show()
    pump(qapp, 300)
    panel.hide()
    pump(qapp, 700)
    assert quits == [1]
    svc.show()           # showing again stops the countdown
    pump(qapp, 300)
    assert panel.bridge.shown
    assert not warnings, warnings


def test_ipc_commands(qapp, controller):
    svc, panel, _ = controller
    assert svc.handle_command("ping") == "pong"
    assert svc.handle_command("toggle") == "ok"
    pump(qapp, 300)
    assert panel.bridge.shown
    assert svc.handle_command("hide") == "ok"
    pump(qapp, 400)
    assert not panel.window.isVisible()
    assert svc.handle_command("nonsense") == "unknown command"
    assert panel.handle_command("ping") == "pong"
    assert svc.handle_command("activate 999999 0 0") == "failed"
