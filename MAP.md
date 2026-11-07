# Clipio — architecture map
A paper-themed clipboard history for Windows, macOS and Linux, written in Python with a Qt Quick (QML) panel through PySide6.

## Folders
- `clipio/` — the Python package
  - `__init__.py`, `__main__.py` — version and `python -m clipio`
  - `cli.py` — the `clipio` command (starts the app, sends it commands, manages items)
  - `app.py` — the running app: `Controller` wires storage, clipboard, panel, hotkey, tray and IPC
  - `bridge.py` — `Backend`, the QML singleton the panel reads state from and sends actions to
  - `ipc.py` — single-instance local socket between `clipio` commands and the running app
  - `core/` — platform-independent logic: paths, settings, SQLite storage, classification, limits
  - `system/` — operating-system integration: clipboard backends, paste keystroke, global hotkey, autostart, Hyprland rule
  - `ui/` — QML window (`Main.qml`), `components/`, `icons/`, `assets/` (logo)
- `tests/` — pytest suite; runs headless (`QT_QPA_PLATFORM=offscreen`)
- `docs/assets/` — images used by the README
- `.github/workflows/ci.yml` — tests on Windows, macOS and Linux with Python 3.10–3.14

## Main flow
1. `clipio start` (or the autostart entry) runs `python -m clipio run` → `app.run()` creates the Qt app, the clipboard backend, the panel and the IPC server.
2. The clipboard backend emits `changed` → `Controller.on_clipboard_changed` reads a `Snapshot` → `core/ingest.py` classifies and saves it → `core/db.py` (SQLite) → `Controller.refresh` publishes `core/export.build_state` through `Backend`.
3. The global hotkey (Windows, macOS, X11) or `clipio toggle` (bound in the desktop; required on Wayland) opens the panel. `ui/components/Store.qml` turns the state into the card list.
4. Picking a card calls `Backend.activate` → `core/actions.copy` puts it on the clipboard → the window hides → `system/paste.Paster` sends Ctrl+V / Cmd+V to the previous app.
5. The settings dialog calls `Backend.setRetention` → `core/config.set_int` writes `config.toml` → `core/maintenance.run` deletes older items right away.

## Platform backends
| Desktop | Clipboard | Paste keystroke | Global hotkey |
| --- | --- | --- | --- |
| Windows | Qt `QClipboard` | Win32 `keybd_event` after restoring focus | Win32 `RegisterHotKey` |
| macOS | Qt `QClipboard` + pasteboard change counter | `osascript` Cmd+V | pynput |
| Linux X11 | Qt `QClipboard` | `xdotool` | `XGrabKey` (python-xlib) |
| Linux Wayland (Hyprland, Sway, KDE) | `wl-paste --watch` / `wl-copy` | `hyprctl` or `wtype` | bind `clipio toggle` in the compositor |
| Linux Wayland without data-control (GNOME) | Qt through XWayland | copy only | bind `clipio toggle` in Settings |

## External locations
- Data: Windows `%LOCALAPPDATA%\clipio`, macOS `~/Library/Application Support/clipio`, Linux `~/.local/share/clipio` (`clipio.db`, `images/`, `paused`)
- Settings: Windows `%APPDATA%\clipio\config.toml`, macOS `~/Library/Application Support/clipio/config.toml`, Linux `~/.config/clipio/config.toml`
- `CLIPIO_DATA_DIR` and `CLIPIO_CONFIG_DIR` override both (used by the tests)
- Autostart: Windows registry `HKCU\...\Run\Clipio`, macOS `~/Library/LaunchAgents/io.github.ardazeybek.clipio.plist`, Linux `~/.config/autostart/clipio.desktop`

## Design
Paper theme: old-notebook paper background, note-paper cards with a paper-stack shadow, mustard tape accents. Peach `accent` for selection, sage `sage` tape for pinned items (`clipio/ui/components/Theme.qml`). The logo (`clipio/ui/assets/clipio.svg`) is two note sheets with a paper clip and tape on a transparent background. The window is frameless and transparent; the panel draws its own shadow. Cards show only their content and time. Clearing and settings use in-panel paper dialogs (`Dialog.qml`).
