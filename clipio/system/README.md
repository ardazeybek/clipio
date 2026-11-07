# clipio/system/
Operating-system integration. Each file hides one platform difference behind a small API.

- `__init__.py` — detects the desktop (`windows`, `macos`, `wayland`, `x11`) and picks the clipboard backend
- `clipboard.py` — `QtClipboard` (Windows, macOS, X11) and `WaylandClipboard` (wl-clipboard)
- `paste.py` — `Paster`: remembers the focused window and sends the paste keystroke
- `active_app.py` — name of the app the user copied from
- `hotkey.py` — `GlobalHotkey`: Win32 `RegisterHotKey`, pynput on macOS, `XGrabKey` on X11
- `autostart.py` — start at login (registry, LaunchAgent, XDG autostart)
- `hyprland.py` — runtime window rule on Hyprland (float, centered, no border or blur)
- `macos.py` — Objective-C runtime helpers (Dock icon, focus, pasteboard counter, Cmd+V)
- `windows.py` — Win32 helpers (focused window, process name, Ctrl+V)
