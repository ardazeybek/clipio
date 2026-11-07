"""Finds the name of the app the user copied from (used for the ignore list)."""
import json
import shutil
import subprocess

from . import is_hyprland, kind


# Run a command and return its text output (empty on failure)
def _out(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


# Window class of the focused Hyprland window
def _hyprland() -> str:
    try:
        return json.loads(_out(["hyprctl", "-j", "activewindow"]) or "{}").get("class", "")
    except json.JSONDecodeError:
        return ""


# Window class of the focused X11 window
def _x11() -> str:
    if shutil.which("xdotool"):
        return _out(["xdotool", "getactivewindow", "getwindowclassname"])
    return ""


# Name of the focused app on this desktop (empty when unknown)
def name() -> str:
    k = kind()
    if k == "windows":
        from . import windows
        return windows.process_name(windows.foreground_window())
    if k == "macos":
        from . import macos
        return macos.frontmost_app()
    if is_hyprland():
        return _hyprland()
    return _x11() if k == "x11" else ""
