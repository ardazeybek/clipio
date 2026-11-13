"""Reads text from an image with the Tesseract OCR program (when it is installed)."""
import shutil
import subprocess
from pathlib import Path

LANGS_PREFERRED = ("tur", "eng")


# True when the tesseract program is installed
def available() -> bool:
    return shutil.which("tesseract") is not None


# Installed languages we want, joined for tesseract (e.g. "tur+eng")
def _langs() -> str:
    try:
        r = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return "eng"
    have = set(r.stdout.split())
    picked = [l for l in LANGS_PREFERRED if l in have]
    return "+".join(picked) or "eng"


# Text found in the image file ('' when nothing was found or OCR failed)
def read_text(image: Path) -> str:
    if not available() or not image.exists():
        return ""
    try:
        r = subprocess.run(["tesseract", str(image), "-", "-l", _langs()],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""
