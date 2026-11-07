"""Sends the paste keystroke to the app that was active before Clipio opened."""
import shutil
import subprocess

from . import active_app, is_hyprland, kind

# Terminals paste with Ctrl+Shift+V on Linux
TERMINALS = {
    "kitty", "alacritty", "foot", "footclient", "wezterm", "org.wezfurlong.wezterm",
    "com.mitchellh.ghostty", "ghostty", "konsole", "org.kde.konsole", "xterm", "urxvt",
    "gnome-terminal-server", "org.gnome.terminal", "org.gnome.ptyxis", "tilix", "terminator",
    "st-256color", "org.kde.yakuake", "xfce4-terminal", "lxterminal", "cool-retro-term", "contour",
}


# Run a command quietly; return True on success
def _run(cmd: list[str]) -> bool:
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and b"error" not in r.stdout.lower()


# Linux modifier list for the focused app
def _linux_mods(app: str) -> list[str]:
    return ["ctrl", "shift"] if app.lower() in TERMINALS else ["ctrl"]


# Build the commands to try for Hyprland (Lua config first, then classic syntax)
def hyprland_commands(mods: list[str]) -> list[list[str]]:
    m = " ".join(x.upper() for x in mods)
    lua = f'hl.dsp.send_shortcut({{mods="{m}", key="V", window="activewindow"}})'
    return [["hyprctl", "dispatch", lua],
            ["hyprctl", "dispatch", "sendshortcut", f"{m.replace(' ', ',')},V,activewindow"]]


# Build the command for X11 (xdotool) or other Wayland compositors (wtype)
def generic_command(k: str, mods: list[str]) -> list[str] | None:
    if k == "x11" and shutil.which("xdotool"):
        return ["xdotool", "key", "--clearmodifiers", "+".join(mods + ["v"])]
    if k == "wayland" and shutil.which("wtype"):
        cmd = ["wtype"]
        for m in mods:
            cmd += ["-M", m]
        cmd += ["v"]
        for m in reversed(mods):
            cmd += ["-m", m]
        return cmd
    return None


class Paster:
    """Remembers the focused window when the panel opens and pastes into it later."""

    def __init__(self):
        self._target = 0

    # Remember the window that has focus right now (Windows needs it to restore focus)
    def remember(self) -> None:
        if kind() == "windows":
            from . import windows
            self._target = windows.foreground_window()

    # True when automatic pasting is available on this desktop
    def available(self) -> bool:
        k = kind()
        if k in ("windows", "macos") or is_hyprland():
            return True
        return generic_command(k, ["ctrl"]) is not None

    # Press the paste keystroke in the remembered app; False when not possible
    def paste(self) -> bool:
        k = kind()
        if k == "windows":
            from . import windows
            windows.focus_window(self._target)
            return windows.send_paste()
        if k == "macos":
            from . import macos
            return macos.send_paste()
        mods = _linux_mods(active_app.name())
        if is_hyprland():
            return any(_run(c) for c in hyprland_commands(mods))
        cmd = generic_command(k, mods)
        return _run(cmd) if cmd else False
