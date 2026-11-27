"""Automatic updates: looks for a newer GitHub release, downloads and checks it, and installs it silently.

Only the packaged app (installed by the setup file) updates itself; a Python install (pipx, pip)
is only told that a new version exists. Everything here runs on a background thread except
`apply()`, which only starts the downloaded installer and returns.
"""
import hashlib
import json
import os
import platform
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .. import __version__
from ..core import paths

REPO = "ardazeybek/clipio"
API = os.environ.get("CLIPIO_UPDATE_API") or f"https://api.github.com/repos/{REPO}/releases/latest"   # override: tests
TIMEOUT = 15
CHUNK = 256 * 1024
SUMS = "SHA256SUMS"


@dataclass
class Update:
    """A newer release: its version and the download links of its files."""
    version: str
    assets: dict   # file name -> download URL


# ---- versions and files ----

# "v1.2.3" -> (1, 2, 3); unknown parts count as 0
def parse_version(text: str) -> tuple:
    parts = []
    for p in text.strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts + [0] * (3 - len(parts)))


# Name of the release file for this computer
def asset_name() -> str:
    if sys.platform == "win32":
        return "Clipio-Setup.exe"
    if sys.platform == "darwin":
        return "Clipio-macOS-Intel.dmg" if platform.machine() == "x86_64" else "Clipio-macOS-AppleSilicon.dmg"
    return "Clipio-Setup-Linux"


# Folder for downloaded updates
def update_dir() -> Path:
    return paths.data_dir() / "updates"


# Marker the new version reads once to say "updated" (holds the old version)
def marker_file() -> Path:
    return paths.data_dir() / "updated-from"


# ---- network ----

# HTTPS settings: the packaged app brings its own certificate list (certifi) when available
def _context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


# Open a URL with Clipio's user agent
def _open(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": f"Clipio/{__version__}",
                                               "Accept": "application/vnd.github+json"})
    return urllib.request.urlopen(req, timeout=TIMEOUT, context=_context())


# The newest release when it is newer than this app, otherwise None (also on network errors)
def check(current: str = __version__) -> Update | None:
    try:
        with _open(API) as r:
            data = json.loads(r.read(1_000_000))
    except Exception:   # offline, rate limited, GitHub down: try again next time
        return None
    if data.get("draft") or data.get("prerelease"):
        return None
    version = str(data.get("tag_name", "")).lstrip("vV")
    if not version or parse_version(version) <= parse_version(current):
        return None
    assets = {a["name"]: a["browser_download_url"] for a in data.get("assets", [])
              if "name" in a and "browser_download_url" in a}
    return Update(version, assets)


# Download this computer's file of an update and verify its checksum; returns the file or None
def download(update: Update) -> Path | None:
    name = asset_name()
    if name not in update.assets or SUMS not in update.assets:
        return None
    folder = update_dir() / update.version
    folder.mkdir(parents=True, exist_ok=True)
    target, part = folder / name, folder / (name + ".part")
    try:
        with _open(update.assets[SUMS]) as r:
            expected = _expected_hash(r.read(100_000).decode("utf-8", "replace"), name)
        if not expected:
            return None
        if not (target.exists() and _sha256(target) == expected):
            digest = hashlib.sha256()
            with _open(update.assets[name]) as r, open(part, "wb") as f:
                while chunk := r.read(CHUNK):
                    digest.update(chunk)
                    f.write(chunk)
            if digest.hexdigest() != expected:   # damaged or changed file: never run it
                part.unlink(missing_ok=True)
                return None
            part.replace(target)
    except Exception:
        part.unlink(missing_ok=True)
        return None
    target.chmod(0o755)
    return target


# Checksum of a file listed in SHA256SUMS ("<hash>  <name>" lines)
def _expected_hash(sums: str, name: str) -> str:
    for line in sums.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == name:
            return parts[0].lower()
    return ""


# SHA-256 of a file on disk
def _sha256(f: Path) -> str:
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


# ---- installing ----

# Command that installs a downloaded update silently (macOS: unpack the app from the disk image first)
def prepare(installer: Path) -> list[str] | None:
    if sys.platform != "darwin":
        return [str(installer), "setup", "--silent"]
    app = installer.parent / "Clipio.app"
    if not app.exists():
        mount = Path(tempfile.mkdtemp(prefix="clipio-dmg-"))
        r = subprocess.run(["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", str(mount), str(installer)],
                           capture_output=True, timeout=120)
        if r.returncode != 0:
            return None
        try:
            copied = subprocess.run(["ditto", str(mount / "Clipio.app"), str(app)], capture_output=True, timeout=300)
        finally:
            subprocess.run(["hdiutil", "detach", str(mount), "-quiet"], capture_output=True, timeout=60)
        # A half-copied app must not be run; remove it so the next try starts clean
        if copied.returncode != 0:
            shutil.rmtree(app, ignore_errors=True)
            return None
    exe = app / "Contents" / "MacOS" / "Clipio"
    return [str(exe), "setup", "--silent"] if exe.exists() else None


# Start the installer detached; it stops this Clipio, swaps the files and starts the new one
def apply(command: list[str], old_version: str = __version__) -> None:
    marker_file().write_text(old_version, encoding="utf-8")
    kwargs: dict = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x00000008 | 0x00000200   # DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    env = {k: v for k, v in os.environ.items() if not k.startswith(("_MEI", "_PYI"))}
    subprocess.Popen(command, env=env, **kwargs)


# After starting: the version this app was updated from ('' when it was not just updated); clears the marker
def take_marker() -> str:
    f = marker_file()
    try:
        old = f.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    f.unlink(missing_ok=True)
    return old if old != __version__ else ""


# Delete downloads of versions that are installed or older
def clean_old() -> None:
    folder = update_dir()
    if not folder.is_dir():
        return
    for d in folder.iterdir():
        if parse_version(d.name) <= parse_version(__version__):
            shutil.rmtree(d, ignore_errors=True)
