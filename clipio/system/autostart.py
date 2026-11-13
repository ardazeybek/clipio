"""Starts Clipio when the user logs in: Windows registry, macOS LaunchAgent, Linux XDG autostart."""
import os
import sys
from pathlib import Path

LABEL = "io.github.ardazeybek.clipio"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# The Python interpreter to start Clipio with (pythonw on Windows: no console window)
def python_exe() -> str:
    exe = Path(sys.executable)
    if sys.platform == "win32":
        w = exe.with_name("pythonw.exe")
        if w.exists():
            return str(w)
    return str(exe)


# Command line that runs Clipio in the background
def command() -> list[str]:
    return [python_exe(), "-m", "clipio", "run"]


# Command line that starts the panel process (the service runs it when the panel opens)
def panel_command() -> list[str]:
    return [python_exe(), "-m", "clipio", "panel"]


# Location of the macOS LaunchAgent file
def mac_plist() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


# Location of the Linux autostart entry
def linux_desktop() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "autostart" / "clipio.desktop"


# macOS LaunchAgent contents
def mac_plist_text() -> str:
    from xml.sax.saxutils import escape
    args = "".join(f"\n        <string>{escape(a)}</string>" for a in command())
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LABEL}</string>
    <key>ProgramArguments</key>
    <array>{args}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""


# Linux autostart entry contents
def linux_desktop_text() -> str:
    exec_line = " ".join(f'"{a}"' if " " in a else a for a in command())
    return f"""[Desktop Entry]
Type=Application
Name=Clipio
Comment=Clipboard history
Exec={exec_line}
Icon=clipio
Terminal=false
X-GNOME-Autostart-enabled=true
"""


# Turn starting at login on or off
def set_enabled(on: bool) -> None:
    if sys.platform == "win32":
        import winreg
        # CreateKeyEx also opens the key when it exists; fresh Windows installs may not have it
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if on:
                value = " ".join(f'"{a}"' if " " in a else a for a in command())
                winreg.SetValueEx(key, "Clipio", 0, winreg.REG_SZ, value)
            else:
                try:
                    winreg.DeleteValue(key, "Clipio")
                except FileNotFoundError:
                    pass
        return
    f, text = (mac_plist(), mac_plist_text) if sys.platform == "darwin" else (linux_desktop(), linux_desktop_text)
    if on:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text(), encoding="utf-8")
    else:
        f.unlink(missing_ok=True)


# True when Clipio starts at login
def is_enabled() -> bool:
    if sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.QueryValueEx(key, "Clipio")
            return True
        except FileNotFoundError:
            return False
    return (mac_plist() if sys.platform == "darwin" else linux_desktop()).exists()
