"""Renders the README pictures from the real QML panel with sample data (headless).

Run from the repository root:  python docs/capture.py
Writes docs/assets/overview.png, settings.png and demo.gif (needs ffmpeg for the GIF).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
WORK = Path(tempfile.mkdtemp(prefix="clipio-capture-"))
os.environ["QT_QPA_PLATFORM"] = "offscreen"       # never a real window
os.environ.setdefault("QT_QUICK_BACKEND", "rhi")    # GPU renderer, so shadows and tinted icons show
os.environ.setdefault("QSG_RHI_BACKEND", "opengl")
os.environ["CLIPIO_DATA_DIR"] = str(WORK / "data")
os.environ["CLIPIO_CONFIG_DIR"] = str(WORK / "config")
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEvent, QObject, QPointF, Qt, QTimer   # noqa: E402
from PySide6.QtGui import QColor, QGuiApplication, QImage, QKeyEvent, QPainter, QPainterPath  # noqa: E402
from PySide6.QtQuick import QQuickWindow   # noqa: E402,F401  (lets grabWindow work)
from PySide6.QtTest import QTest   # noqa: E402

BACKDROP = QColor("#EDE4D3")   # warm desk color behind the panel in the GIF
FRAME_MS = 50                  # 20 frames per second


# Draw the sample landscape picture (peach sky, sun, green hills) as PNG bytes
def landscape_png() -> bytes:
    from PySide6.QtCore import QBuffer, QIODevice
    img = QImage(900, 360, QImage.Format.Format_RGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.fillRect(img.rect(), QColor("#F2C4A4"))
    p.setBrush(QColor("#FCE6C0"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(620, 110), 70, 70)
    for color, base, amp in (("#9CC3A6", 230, 40), ("#79A88A", 270, 30), ("#5E8C72", 310, 25)):
        path = QPainterPath(QPointF(0, base))
        path.cubicTo(250, base - amp, 500, base + amp, 900, base - amp / 2)
        path.lineTo(900, 360)
        path.lineTo(0, 360)
        p.setBrush(QColor(color))
        p.drawPath(path)
    p.end()
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


# Fill the database with the sample items shown in the pictures (newest last)
def seed(con) -> None:
    from clipio.core import config, ingest
    from clipio.core.ingest import Snapshot
    cfg = config.load()
    now = time.time()
    samples = [  # (text or None for the image, source app, minutes ago, pinned)
        (None, "Firefox", 50, False),
        ("git switch -c feature/paper-theme\ngit commit -m \"Add paper theme\"\n"
         "git push -u origin feature/paper-theme", "kitty", 25, False),
        ("#E58F6F", "Figma", 5, False),
        ("https://github.com/ardazeybek/clipio", "Firefox", 0.2, False),
        ("Meeting moved to Thursday 14:00 — room 3B", "Slack", 90, True),
    ]
    for text, app, ago, pinned in samples:
        snap = Snapshot(formats=["image/png"], image=landscape_png(), image_mime="image/png") if text is None \
            else Snapshot(formats=["text/plain"], text=text.encode())
        item_id = ingest.capture(con, snap, app, cfg)
        t = now - ago * 60
        con.execute("UPDATE items SET created=?, used=?, pinned=? WHERE id=?", (t, t, int(pinned), item_id))
    con.commit()


# Flatten a transparent window grab onto the desk color
def flat(img: QImage) -> QImage:
    out = QImage(img.size(), QImage.Format.Format_RGB32)
    out.fill(BACKDROP)
    p = QPainter(out)
    p.drawImage(0, 0, img)
    p.end()
    return out


class Recorder:
    """Plays a list of (delay ms, action) steps on the panel and grabs a frame every FRAME_MS."""

    def __init__(self, app, panel):
        self.app, self.panel = app, panel
        self.win = panel.engine.rootObjects()[0]
        self.frames: list[QImage] = []
        self.stamps: list[float] = []   # when each frame was grabbed (grabs can be slower than FRAME_MS)
        self.recording = False
        self._tick = QTimer()
        self._tick.timeout.connect(self._grab)

    # Grab one frame while recording
    def _grab(self) -> None:
        if self.recording:
            self.frames.append(flat(self.win.grabWindow()))
            self.stamps.append(time.monotonic())

    # Run the steps one after another, then call done()
    def play(self, steps, done) -> None:
        self._tick.start(FRAME_MS)
        t = 0
        for delay, action in steps:
            t += delay
            QTimer.singleShot(t, action)
        QTimer.singleShot(t + 50, done)

    # Press one key in the panel window
    def key(self, key, mods=Qt.KeyboardModifier.NoModifier) -> None:
        QTest.keyClick(self.win, key, mods)

    # Type one character into the search field
    def type(self, ch: str) -> None:
        key = Qt.Key(ord(ch.upper()))
        for kind in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            QGuiApplication.sendEvent(self.win, QKeyEvent(kind, key, Qt.KeyboardModifier.NoModifier, ch))


# Find the settings page item of the panel
def settings_item(win):
    for o in win.findChildren(QObject):
        if o.metaObject().className().startswith("Settings"):
            return o
    return None


# Build the GIF from the recorded frames with ffmpeg (two-pass palette for clean colors)
def write_gif(frames: list[QImage], stamps: list[float], target: Path) -> None:
    if not shutil.which("ffmpeg"):
        print("ffmpeg not found: demo.gif skipped")
        return
    folder = WORK / "frames"
    folder.mkdir()
    for i, f in enumerate(frames):
        f.scaledToWidth(f.width() * 3 // 4, Qt.TransformationMode.SmoothTransformation).save(
            str(folder / f"{i:04d}.png"))
    pattern = str(folder / "%04d.png")
    palette = str(WORK / "palette.png")
    fps = f"{(len(stamps) - 1) / max(stamps[-1] - stamps[0], 0.1):.2f}"   # real speed
    base = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-framerate", fps, "-i", pattern]
    subprocess.run([*base, "-vf", "palettegen=stats_mode=diff", palette], check=True, stdin=subprocess.DEVNULL)
    subprocess.run([*base, "-i", palette, "-lavfi", "paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                    "-loop", "0", str(target)], check=True, stdin=subprocess.DEVNULL)


# Render every picture
def main() -> int:
    app = QGuiApplication(sys.argv[:1])
    from clipio.panel import PanelController
    panel = PanelController(app, service=lambda c: "ok" if c.startswith(("panel", "activate")) else "")
    seed(panel.con)
    if not panel.load_ui():
        print("the panel could not be loaded", file=sys.stderr)
        return 1
    panel._center_window = lambda: None
    rec = Recorder(app, panel)
    win = rec.win
    ASSETS.mkdir(parents=True, exist_ok=True)

    # Save a still picture of the window (transparent around the panel)
    def still(name):
        return lambda: win.grabWindow().save(str(ASSETS / name))

    def open_settings():
        s = settings_item(win)
        s.setProperty("page", "guide")
        s.setProperty("shown", True)

    def settings_page(page):
        return lambda: settings_item(win).setProperty("page", page)

    def close_settings():
        settings_item(win).setProperty("shown", False)

    def start():
        rec.recording = True
        panel.show()

    def stop():
        rec.recording = False

    down = lambda: rec.key(Qt.Key.Key_Down)   # noqa: E731
    up = lambda: rec.key(Qt.Key.Key_Up)       # noqa: E731
    steps = [
        (300, start), (900, still("overview.png")),
        (500, down), (450, down), (450, down), (450, up), (450, up), (450, up),
        *[(170, (lambda c=c: rec.type(c))) for c in "git"], (1300, lambda: rec.key(Qt.Key.Key_Escape)),
        *[(170, (lambda c=c: rec.type(c))) for c in "#e5"], (1300, lambda: rec.key(Qt.Key.Key_Escape)),
        (600, open_settings), (1600, settings_page("features")), (1400, settings_page("storage")),
        (300, still("settings.png")), (1400, close_settings), (900, stop),
    ]
    rec.play(steps, app.quit)
    app.exec()
    write_gif(rec.frames, rec.stamps, ASSETS / "demo.gif")
    print(f"{len(rec.frames)} frames; pictures in {ASSETS}")
    shutil.rmtree(WORK, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
