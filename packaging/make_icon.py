"""Renders the Clipio logo (clipio/ui/assets/clipio.svg) to build/icon.png for the app icons."""
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
SIZE = 1024


# Draw the SVG onto a transparent square image and save it as PNG
def render(out: Path) -> None:
    img = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    QSvgRenderer(str(ROOT / "clipio/ui/assets/clipio.svg")).render(p)
    p.end()
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out))


if __name__ == "__main__":
    app = QGuiApplication(sys.argv[:1])
    render(ROOT / "build" / "icon.png")
