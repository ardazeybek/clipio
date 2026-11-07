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


@pytest.fixture(scope="session")
def ui(qapp, tmp_path_factory):
    """One controller and one QML engine for the whole session (Qt allows only one
    engine to use the Backend singleton)."""
    from clipio.app import Controller
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
    ctl = Controller(qapp, StubClipboard())
    assert ctl.load_ui(), warnings
    yield ctl, warnings, base
    ctl.window.hide()
    qInstallMessageHandler(previous)
    mp.undo()


@pytest.fixture
def controller(ui, monkeypatch):
    ctl, warnings, base = ui
    # use the session folders the controller's database lives in, not the per-test ones
    monkeypatch.setenv("CLIPIO_DATA_DIR", str(base / "data"))
    monkeypatch.setenv("CLIPIO_CONFIG_DIR", str(base / "config"))
    ctl.con.execute("DELETE FROM items")
    ctl.con.commit()
    seed(ctl.con)
    ctl.refresh()
    warnings.clear()
    yield ctl, warnings
    ctl.hide()


def test_panel_loads_and_lists_items(qapp, controller):
    ctl, warnings = controller
    ctl.show()
    pump(qapp, 700)
    assert ctl.window.isVisible()
    assert ctl.bridge.shown
    assert not warnings, warnings


def test_new_clipboard_content_is_saved(qapp, controller):
    ctl, warnings = controller
    ctl.clipboard.snap = Snapshot(formats=["text/plain"], text=b"fresh copy")
    ctl.on_clipboard_changed()
    rows = db.list_items(ctl.con)
    assert any(r["text"] == "fresh copy" for r in rows)
    assert not warnings, warnings


def test_actions_from_the_panel(qapp, controller):
    ctl, warnings = controller
    ctl.show()
    pump(qapp, 300)
    first = db.list_items(ctl.con)[0]["id"]
    ctl.bridge.togglePin(first)
    assert db.get(ctl.con, first)["pinned"] == 1
    ctl.bridge.setRetention(7)
    assert config.load()["retention_days"] == 7
    ctl.bridge.setPaused(True)
    ctl.bridge.setPaused(False)
    ctl.bridge.activate(first, False)        # copy only
    pump(qapp, 300)
    assert not ctl.clipboard.snap.is_empty()
    assert not ctl.bridge.shown
    ctl.bridge.clearAll()
    assert all(r["pinned"] for r in db.list_items(ctl.con))
    pump(qapp, 300)
    assert not warnings, warnings


def test_ipc_commands(qapp, controller):
    ctl, _ = controller
    assert ctl.handle_command("ping") == "pong"
    assert ctl.handle_command("toggle") == "ok"
    pump(qapp, 300)
    assert ctl.bridge.shown
    assert ctl.handle_command("hide") == "ok"
    pump(qapp, 400)
    assert not ctl.window.isVisible()
    assert ctl.handle_command("nonsense") == "unknown command"
