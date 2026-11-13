"""Operating-system integration: clipboard, paste keystroke, global shortcut, autostart."""
import functools
import os
import shutil
import subprocess
import sys
import time


# Return the desktop kind: "windows", "macos", "wayland" or "x11"
def kind() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if os.environ.get("WAYLAND_DISPLAY") and os.environ.get("QT_QPA_PLATFORM", "") != "xcb":
        return "wayland"
    return "x11"


# True when running under Hyprland
def is_hyprland() -> bool:
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))


# True when `wl-paste --watch` works (the compositor supports the data-control protocol)
@functools.lru_cache(maxsize=1)
def wayland_watch_supported() -> bool:
    if not shutil.which("wl-paste") or not shutil.which("wl-copy"):
        return False
    try:
        proc = subprocess.Popen(["wl-paste", "--watch", "true"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    time.sleep(0.4)
    alive = proc.poll() is None
    if alive:
        proc.kill()
        proc.wait()
    return alive


# Choose the Qt platform before the app starts: on Wayland without data-control
# (for example GNOME) run through XWayland so the clipboard can be watched
def prepare_qt_env() -> None:
    if os.environ.get("CLIPIO_QPA_CHECKED"):   # the service already decided for its panel process
        return
    os.environ["CLIPIO_QPA_CHECKED"] = "1"
    if sys.platform.startswith("linux") and os.environ.get("WAYLAND_DISPLAY") \
            and "QT_QPA_PLATFORM" not in os.environ \
            and os.environ.get("DISPLAY") and not wayland_watch_supported():
        os.environ["QT_QPA_PLATFORM"] = "xcb"


# Create the clipboard backend that fits this desktop
def create_clipboard(app):
    from . import clipboard
    if kind() == "wayland" and wayland_watch_supported():
        return clipboard.WaylandClipboard()
    return clipboard.QtClipboard(app.clipboard())
