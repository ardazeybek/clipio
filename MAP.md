# Clipio — architecture map
A paper-themed clipboard history for Windows, macOS and Linux, written in Python with a Qt Quick (QML) panel through PySide6.

## Folders
- `clipio/` — the Python package
  - `__init__.py`, `__main__.py` — version and `python -m clipio`
  - `cli.py` — the `clipio` command (starts the service, sends it commands, manages items)
  - `app.py` — the background service: `Controller` wires storage, clipboard, paste keystroke, hotkey, tray, IPC and the panel link (no QML)
  - `panel_link.py` — service side of the panel: starts `clipio panel` on demand, sends it commands without waiting
  - `panel.py` — the panel process: `PanelController` loads the QML window, quits `panel_keep_minutes` after closing
  - `bridge.py` — `Backend`, the QML singleton the panel reads state from and sends actions to
  - `ipc.py` — local sockets: service channel (`clipio-<user>`) and panel channel (`clipio-<user>-panel`); `send` waits, `post` does not
  - `core/` — platform-independent logic: paths, settings, SQLite storage, classification, limits
  - `system/` — operating-system integration: clipboard backends, paste keystroke, global hotkey, autostart, Hyprland rule
  - `ui/` — QML window (`Main.qml`), `components/`, `icons/`, `assets/` (logo)
- `tests/` — pytest suite; runs headless (`QT_QPA_PLATFORM=offscreen`); `test_e2e.py` runs real service and panel processes
- `docs/` — `capture.py` renders the README pictures; `assets/` holds them (overview, demo GIF, settings)
- `.github/` — `workflows/ci.yml` (tests on Windows, macOS and Linux with Python 3.10–3.14), issue and pull request templates
- `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` — community files GitHub shows on the repo page

## Two processes (memory)
- **Service** (`clipio run`): always on, ~25 MB of its own memory (the rest is shared Python/Qt libraries). Clipboard, saving, paste keystroke, hotkey, tray, `clipio` commands, paste queue. Never imports QtQml/QtQuick. Gives freed memory back after big items and hourly (`system/memory.py`).
- **Panel** (`clipio panel`): QML + graphics driver + fonts (~150–350 MB). Started by `PanelLink` when the panel opens, quits by itself `panel_keep_minutes` (default 5, 0 = at once, 1440 = always ready) after closing. First open after that takes about a second.
- They share the SQLite database (WAL). The panel reads and changes items itself; copying, pasting and the queue go to the service (`activate <id> <paste> <clean>`, `queue …`, `queue?`, `next`, `clearqueue`). The panel reports `panel ready|shown|hidden|exit`.
- No deadlocks: the panel may wait for the service (`ipc.send`), the service never waits for the panel (`ipc.post`).
- Windows: the service calls `AllowSetForegroundWindow` before showing, so the panel process may take focus. macOS: the panel hides its own app to give focus back, then the service sends Cmd+V.

## Main flow
1. `clipio start` (or the autostart entry) runs `python -m clipio run` → `app.run()` creates the Qt app, the clipboard backend and the IPC server (no panel yet).
2. The clipboard backend emits `changed` → `Controller.on_clipboard_changed` reads a `Snapshot` → `core/ingest.py` classifies and saves it → `core/db.py` (SQLite) → `Controller.refresh` tells an open panel to reload (`core/export.build_state`, published through `Backend`).
3. On Hyprland the panel takes focus itself (`hyprctl`) and ignores the focus Hyprland hands back to the window under the mouse right after opening. Tools that kill apps whose windows close (like `pencere-kapat`) must exclude the `clipio` class, because hiding the panel unmaps its window.
4. The global hotkey (Windows, macOS, X11) or `clipio toggle` (bound in the desktop; required on Wayland) → `PanelLink.show` remembers the focused window, then tells the panel process to show (or starts it). `ui/components/Store.qml` turns the state into the card list.
5. Picking a card calls `Backend.activate` → the panel sends `activate` to the service → `core/actions.copy` puts it on the clipboard → the panel window hides → `system/paste.Paster` sends Ctrl+V / Cmd+V to the previous app.
6. The settings dialog calls `Backend.setRetention` → `core/config.set_int` writes `config.toml` → `core/maintenance.run` deletes older items right away.

## Extra features
- Card menu (right-click or Ctrl+M): paste cleaned (also Shift+Enter), copy only (Ctrl+C), edit then paste (Ctrl+E), conversions (`core/transform.py`), folder (`db.set_tag`, folder chips in the Pinned tab), OCR for images (`system/ocr.py`), "don't save from this app" (`ignore_apps`).
- Paste queue: Ctrl+click or Ctrl+Space marks cards; Enter pastes the first and loads the next; `clipio next` (bind a key) pastes the rest. Kept in `Controller.queue`.
- Alt+1…9 pastes the first nine cards; holding Alt shows the numbers.
- On capture (`core/ingest.py`): links lose tracking parameters (`clean_links`), secrets get `secret=1` and are hidden and deleted after `secret_minutes`, password manager apps are skipped.
- Pinned snippets with `{date}`, `{time}`, `{clipboard}`… are filled when pasted (`core/template.py`).
- Smart cards: color swatch with the other notation, link page titles (`link_titles`, off by default), colored code (`core/highlight.py`), source app line; `@app` in search filters by app.
- Background jobs hand results to the main thread: OCR runs in the panel (`Bridge.post`), link titles in the service (`_Relay`).

## Settings page
- `ui/components/Settings.qml` (gear button or `Ctrl+,`): tabs How to (animated `GuideDemo` per feature), Shortcuts, Features, Storage.
- Shortcuts: `config.SHORTCUTS` defaults, saved as `key_<action>` in `config.toml`; `Store.actionFor(event)` maps a key press to an action and `Panel.runAction` runs it. Arrows, PgUp/PgDn and Esc stay fixed.
- Storage: retention days, how long the closed panel stays loaded (`panel_keep_minutes`), ignored apps.
- Features: `config.FEATURES` switches (clean links, secrets, templates, code colors, source app, Alt numbers, link titles), read in `ingest`, `actions`, `export` and the QML.

## Platform backends
| Desktop | Clipboard | Paste keystroke | Global hotkey |
| --- | --- | --- | --- |
| Windows | Qt `QClipboard` | Win32 `keybd_event` after restoring focus | Win32 `RegisterHotKey` |
| macOS | Qt `QClipboard` + pasteboard change counter | `osascript` Cmd+V | pynput |
| Linux X11 | Qt `QClipboard` | `xdotool` | `XGrabKey` (python-xlib) |
| Linux Wayland (Hyprland, Sway, KDE) | `wl-paste --watch` / `wl-copy` | `hyprctl` or `wtype` | bind `clipio toggle` in the compositor |
| Linux Wayland without data-control (GNOME) | Qt through XWayland | copy only | bind `clipio toggle` in Settings |

## External locations
- Data: Windows `%LOCALAPPDATA%\clipio`, macOS `~/Library/Application Support/clipio`, Linux `~/.local/share/clipio` (`clipio.db`, `images/`, `paused`, `clipio.lock` — only one Clipio runs at a time)
- Panel lock: `panel.lock` in the data folder (one panel process at a time)
- Settings: Windows `%APPDATA%\clipio\config.toml`, macOS `~/Library/Application Support/clipio/config.toml`, Linux `~/.config/clipio/config.toml`
- `CLIPIO_DATA_DIR` and `CLIPIO_CONFIG_DIR` override both (used by the tests)
- Autostart: Windows registry `HKCU\...\Run\Clipio`, macOS `~/Library/LaunchAgents/io.github.ardazeybek.clipio.plist`, Linux `~/.config/autostart/clipio.desktop`

## Design
Paper theme: old-notebook paper background, note-paper cards with a paper-stack shadow, mustard tape accents. Peach `accent` for selection, sage `sage` tape for pinned items (`clipio/ui/components/Theme.qml`). The logo (`clipio/ui/assets/clipio.svg`) is two note sheets with a paper clip and tape on a transparent background. The window is frameless and transparent; the panel draws its own shadow. On Hyprland a runtime rule (re-added every time the panel opens, because `hyprctl reload` drops runtime rules) turns off the compositor border, blur, shadow and 0.57+ inner glow, which would otherwise outline the transparent window. Cards show only their content and time. Clearing and settings use in-panel paper dialogs (`Dialog.qml`).
