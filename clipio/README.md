# clipio/
The Python package. Clipio runs as two processes:

- **service** (`clipio run`, `app.py`) — always running and small: watches the clipboard, saves items, pastes, owns the hotkey, tray and the `clipio` command channel. It never loads QML or the graphics driver.
- **panel** (`clipio panel`, `panel.py`) — started by the service when the panel opens; quits by itself `panel_keep_minutes` after it was closed, which frees most of Clipio's memory.

Files:
- `__init__.py`, `__main__.py` — version and `python -m clipio`
- `cli.py` — the `clipio` command (starts the service, sends it commands, manages items)
- `app.py` — the service: `Controller` wires storage, clipboard, paste keystroke, hotkey, tray, IPC and the panel link
- `panel_link.py` — service side of the panel: starts the panel process and sends it commands without ever waiting for it
- `panel.py` — the panel process: `PanelController` loads the QML window, changes the database and asks the service to copy and paste
- `bridge.py` — `Backend`, the QML singleton the panel reads state from and sends actions to
- `ipc.py` — local sockets: the service channel and the panel channel, waiting (`send`) and fire-and-forget (`post`); long names are shortened to fit macOS
- `setup/` — installer of the packaged app: `install.py` (install, update, remove per OS) and `window.py` (the animated setup window, `clipio setup` / `clipio uninstall`, `--silent` for scripts and stores)
- `core/` — platform-independent logic (see its README)
- `system/` — operating-system integration (see its README)
- `ui/` — QML window and components
