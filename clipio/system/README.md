# clipio/system/
Operating-system integration. Each file hides one platform difference behind a small API.

- `__init__.py` — detects the desktop (`windows`, `macos`, `wayland`, `x11`) and picks the clipboard backend
- `clipboard.py` — `QtClipboard` (Windows, macOS, X11) and `WaylandClipboard` (wl-clipboard)
- `paste.py` — `Paster`: remembers the focused window and sends the paste keystroke
- `active_app.py` — name of the app the user copied from
- `hotkey.py` — `GlobalHotkey`: Win32 `RegisterHotKey`, pynput on macOS, `XGrabKey` on X11
- `autostart.py` — start at login (registry, LaunchAgent, XDG autostart); also the command lines of the service and the panel process
- `hyprland.py` — runtime window rule on Hyprland (float, centered, no border, blur, shadow or inner glow; retries without `no_glow` before 0.57); gives the panel focus and reads the cursor position
- `macos.py` — Objective-C runtime helpers (Dock icon, focus, pasteboard counter, Cmd+V)
- `windows.py` — Win32 helpers (focused window, process name, Ctrl+V, letting the panel process take focus)
- `memory.py` — gives freed memory back to the OS (glibc `malloc_trim`, macOS zone relief, Windows working set)
- `ocr.py` — reads text from image items with Tesseract (only when it is installed)
- `linktitle.py` — fetches a copied link's page title in the background (only when `link_titles` is on)
