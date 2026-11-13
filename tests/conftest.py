"""Shared test setup: every test gets its own data and config folders and a headless Qt."""
import os
import sys

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"   # no real screen needed


# Point Clipio at empty temporary folders for each test
@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("CLIPIO_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("CLIPIO_CONFIG_DIR", str(tmp_path / "config"))
    # never talk to a Clipio that is really running on this machine
    monkeypatch.setenv("CLIPIO_IPC_NAME", f"clipio-test-{os.getpid()}-{tmp_path.name}")
    return tmp_path


# A database connection in the temporary folder
@pytest.fixture
def con():
    from clipio.core import db
    c = db.connect()
    yield c
    c.close()


class FakeClipboard:
    """Clipboard backend stand-in that remembers what was written to it."""

    def __init__(self):
        self.text = None
        self.image = None

    # Remember written text
    def write_text(self, text):
        self.text = text
        return True

    # What is on the clipboard now, as a backend would return it
    def read(self):
        from clipio.core.ingest import Snapshot
        return Snapshot(formats=["text/plain"], text=self.text.encode() if self.text else None)

    # Remember a written image
    def write_image(self, data, mime):
        self.image = (data, mime)
        return True


# A fake clipboard backend
@pytest.fixture
def fake_clipboard():
    return FakeClipboard()


# One QApplication for the whole test session (Qt allows only one)
@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv[:1])
    yield app
