"""Clipboard backends: Qt's clipboard (Windows, macOS, X11) and wl-clipboard (Wayland)."""
import subprocess
import sys
import threading
import time

from PySide6.QtCore import QBuffer, QIODevice, QMimeData, QObject, QTimer, Signal
from PySide6.QtGui import QImage

from ..core.ingest import Snapshot

TEXT_TYPES = ("text/plain;charset=utf-8", "text/plain", "UTF8_STRING", "STRING", "TEXT")
IMAGE_TYPES = ("image/png", "image/jpeg", "image/webp", "image/gif", "image/bmp")


# Encode a QImage as PNG bytes
def _png_bytes(image: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    image.save(buf, "PNG")
    return bytes(buf.data())


class QtClipboard(QObject):
    """Uses QClipboard. On macOS the pasteboard change counter is polled because
    Qt only reports changes from other apps when Clipio itself is active."""
    changed = Signal()

    def __init__(self, qclipboard, parent=None):
        super().__init__(parent)
        self._cb = qclipboard
        self._cb.dataChanged.connect(self.changed)
        self._last_count = None
        if sys.platform == "darwin":
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._poll)
            self._timer.start(400)

    # Emit `changed` when the macOS pasteboard counter moves
    def _poll(self) -> None:
        from . import macos
        count = macos.change_count()
        if count is None:
            return
        if self._last_count is not None and count != self._last_count:
            self.changed.emit()
        self._last_count = count

    # Read the current clipboard content
    def read(self) -> Snapshot:
        md = self._cb.mimeData()
        if md is None:
            return Snapshot()
        snap = Snapshot(formats=list(md.formats()))
        if md.hasText() and md.text():
            snap.text = md.text().encode("utf-8")
            return snap
        raw_type = next((t for t in IMAGE_TYPES if md.hasFormat(t)), None)
        if raw_type:
            snap.image, snap.image_mime = bytes(md.data(raw_type)), raw_type
        elif md.hasImage():
            image = self._cb.image()
            if not image.isNull():
                snap.image, snap.image_mime = _png_bytes(image), "image/png"
        return snap

    # Put text on the clipboard
    def write_text(self, text: str) -> bool:
        self._cb.setText(text)
        return True

    # Put an image on the clipboard (raw bytes plus a decoded image for other apps)
    def write_image(self, data: bytes, mime: str) -> bool:
        image = QImage.fromData(data)
        md = QMimeData()
        md.setData(mime, data)
        if not image.isNull():
            md.setImageData(image)
        self._cb.setMimeData(md)
        return True

    # Stop watching (nothing to clean up for Qt)
    def stop(self) -> None:
        pass


# Run a command and return stdout bytes (None on failure)
def _run(cmd: list[str], data: bytes | None = None, timeout: float = 5):
    try:
        r = subprocess.run(cmd, input=data, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


# Feed data to wl-copy. Its forked helper keeps running to serve the clipboard, so
# its output must not be a pipe (waiting for that pipe to close would block Clipio)
def _wl_copy(args: list[str], data: bytes) -> bool:
    try:
        proc = subprocess.Popen(["wl-copy", *args], stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.communicate(data, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


class WaylandClipboard(QObject):
    """Uses wl-clipboard, which can watch the clipboard in the background on
    compositors with the data-control protocol (Hyprland, Sway, KDE Plasma)."""
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop = threading.Event()
        self._proc = None
        threading.Thread(target=self._watch, daemon=True).start()

    # Follow `wl-paste --watch` and emit `changed` for every new selection
    def _watch(self) -> None:
        cmd = ["wl-paste", "--watch", "sh", "-c", "cat >/dev/null; echo c"]
        while not self._stop.is_set():
            try:
                self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
            except OSError:
                return
            for _ in self._proc.stdout:
                self.changed.emit()
            self._proc.wait()
            time.sleep(2)   # restart shortly if the watcher died

    # Read the current clipboard content
    def read(self) -> Snapshot:
        out = _run(["wl-paste", "--list-types"])
        types = out.decode(errors="replace").split() if out else []
        snap = Snapshot(formats=types)
        text_t = next((t for t in TEXT_TYPES if t in types), None)
        if text_t:
            snap.text = _run(["wl-paste", "--no-newline", "--type", text_t], timeout=10)
            return snap
        img_t = "image/png" if "image/png" in types else \
            next((t for t in types if t.startswith("image/")), None)
        if img_t:
            snap.image, snap.image_mime = _run(["wl-paste", "--type", img_t], timeout=10), img_t
        return snap

    # Put text on the clipboard
    def write_text(self, text: str) -> bool:
        return _wl_copy(["--type", "text/plain;charset=utf-8"], text.encode())

    # Put an image on the clipboard
    def write_image(self, data: bytes, mime: str) -> bool:
        return _wl_copy(["--type", mime], data)

    # Stop the watcher process
    def stop(self) -> None:
        self._stop.set()
        if self._proc:
            self._proc.terminate()
