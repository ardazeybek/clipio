<div align="center">
  <img src="clipio/ui/assets/clipio.svg" alt="Clipio logo" width="96" />
  <h1>Clipio</h1>
  <p><strong>Find and paste anything you copied earlier, with one shortcut.</strong></p>
  <p>A paper-themed clipboard history for Windows, macOS and Linux that remembers your text, links, colors, code and images.</p>
  <p>
    <a href="https://github.com/ardazeybek/clipio/actions/workflows/ci.yml"><img src="https://github.com/ardazeybek/clipio/actions/workflows/ci.yml/badge.svg" alt="Test status" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-E58F6F" alt="MIT license" /></a>
    <img src="https://img.shields.io/badge/python-3.10%E2%80%933.14-9CC3A6" alt="Python 3.10 to 3.14" />
  </p>
  <p><a href="#quick-start">Quick start</a> · <a href="#usage">Usage</a> · <a href="CONTRIBUTING.md">Contribute</a> · <a href="mailto:quantastudio.dev@gmail.com">Contact</a></p>
</div>

<p align="center">
  <img src="docs/assets/overview.png" alt="The Clipio panel showing a pinned note, a link, a color, a code snippet and an image in a list of paper cards" width="440" />
</p>

<p align="center"><em>The real Clipio panel with sample data: a pinned note, a link, a color, two lines of code and a copied image.</em></p>

## What is Clipio?

Clipio keeps a history of what you copy. Press the shortcut, pick an earlier item, and Clipio pastes it into the window you were using.

It is made for people who copy the same things again and again and want a simple, good-looking way to get them back. Everything stays on your computer in a local SQLite database. Unpinned items are deleted automatically after the number of days you choose.

Clipio runs on **Windows 10/11, macOS and Linux** (X11 and Wayland). It is written in Python with a Qt Quick interface through PySide6.

## Features

- **One-shortcut history** — Open the panel, choose an item and it is pasted into the app you were using.
- **Readable cards** — Links, colors, code and images each get their own card, so you can recognise an item at a glance.
- **Search and tabs** — Type to filter, or switch between All, Text, Images and Pinned.
- **Pins that stay** — Pin the things you reuse. Pinned items are never deleted automatically or by *Clear*.
- **Automatic cleanup** — Choose how long items are kept (1, 3, 7, 14 or 30 days) in the settings window.
- **Privacy controls** — Pause recording at any time, list apps whose copies are never saved, and copies that password managers mark as secret are skipped.

## Usage

1. Copy something in any app as usual.
2. Press the shortcut. The panel opens in the middle of the screen.
3. Type to search, or use the arrow keys to move between cards.
4. Press <kbd>Enter</kbd> or click a card. Clipio closes and pastes it.

| Desktop | Default shortcut |
| --- | --- |
| Windows | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd> |
| macOS | <kbd>⌘</kbd> + <kbd>⇧</kbd> + <kbd>V</kbd> |
| Linux X11 | <kbd>Super</kbd> + <kbd>V</kbd> |
| Linux Wayland | none built in: bind `clipio toggle` yourself (see [Wayland](#wayland)) |

Inside the panel:

| Key | Action |
| --- | --- |
| <kbd>↑</kbd> <kbd>↓</kbd> · <kbd>PgUp</kbd> <kbd>PgDn</kbd> | Move the selection |
| <kbd>Enter</kbd> · left click | Paste the selected item |
| <kbd>Shift</kbd> + <kbd>Enter</kbd> · right click | Copy it without pasting |
| <kbd>Alt</kbd> + <kbd>1</kbd>–<kbd>9</kbd> | Paste one of the first nine items |
| <kbd>Ctrl</kbd> + <kbd>P</kbd> (<kbd>⌘</kbd> + <kbd>P</kbd> on macOS) | Pin or unpin |
| <kbd>Del</kbd> | Delete the selected item |
| <kbd>Tab</kbd> · <kbd>Shift</kbd> + <kbd>Tab</kbd> | Next or previous tab |
| <kbd>Esc</kbd> | Clear the search, then close |

The buttons next to the search field pause recording, clear the history (after a confirmation) and open the settings. Drag the panel by any empty spot. Clicking outside it closes it. On Windows and macOS, Clipio also has a tray or menu-bar icon with *Pause recording*, *Start at login* and *Quit*.

## Quick start

There is no packaged release yet. Clipio installs from this repository with pip. The commands are the same on every system.

### Requirements

- Python 3.10 to 3.14 ([python.org](https://www.python.org/downloads/) on Windows and macOS)
- [pipx](https://pipx.pypa.io/) is recommended; plain `pip` works too
- Linux only: on Wayland, `wl-clipboard` is needed (`wl-copy`, `wl-paste`); on X11, `xdotool` is needed for automatic pasting

PySide6 (Qt) and the other Python packages are installed automatically.

### Install

```bash
pipx install git+https://github.com/ardazeybek/clipio.git
```

Then start it and let it start with your session:

```bash
clipio start
clipio autostart on
```

`clipio start` runs Clipio in the background. Copy something, press the shortcut, and the panel opens.

### Permissions on macOS

macOS asks for two permissions the first time:

- **Input Monitoring** for the global shortcut.
- **Accessibility** for pasting into other apps.

Allow both for the terminal or Python that runs Clipio under *System Settings → Privacy & Security*, then run `clipio stop` and `clipio start` again. Without Accessibility, picking an item still copies it, and you paste with <kbd>⌘</kbd> + <kbd>V</kbd>.

### Wayland

Wayland does not let apps register global shortcuts, so bind `clipio toggle` in your desktop:

- **Hyprland** (`hyprland.conf`):
  ```ini
  exec-once = clipio start
  bind = SUPER, V, exec, clipio toggle
  ```
  On Hyprland, Clipio adds a window rule for itself while it runs, so the panel floats in the middle without borders or blur.
- **Sway**: `bindsym $mod+v exec clipio toggle`
- **GNOME and KDE**: add a custom keyboard shortcut in *Settings* with the command `clipio toggle`.

Automatic pasting needs a compositor that accepts simulated keys. It works on Hyprland, and with [`wtype`](https://github.com/atx/wtype) on Sway and other wlroots compositors. On GNOME, Clipio watches the clipboard through XWayland and only copies the item, so you paste with <kbd>Ctrl</kbd> + <kbd>V</kbd>.

### Settings

The first run creates `config.toml` in the settings folder. The retention period can also be changed in the panel's settings window.

| System | Settings file | History |
| --- | --- | --- |
| Windows | `%APPDATA%\clipio\config.toml` | `%LOCALAPPDATA%\clipio\` |
| macOS | `~/Library/Application Support/clipio/config.toml` | `~/Library/Application Support/clipio/` |
| Linux | `~/.config/clipio/config.toml` | `~/.local/share/clipio/` |

| Setting | What it does | Default |
| --- | --- | --- |
| `retention_days` | Days before unpinned items are deleted | `14` |
| `max_items` | Maximum number of stored items | `500` |
| `max_text_kb` | Larger texts are not saved | `1024` |
| `max_image_mb` | Larger images are not saved | `25` |
| `max_images_total_mb` | Total size limit for all images | `1024` |
| `persist` | Put the last item back when the source app empties the clipboard | `true` |
| `hotkey` | Global shortcut, e.g. `"ctrl+alt+v"` | see the table above |
| `ignore_apps` | Apps whose copies are never saved, e.g. `["KeePassXC", "1Password"]` | `[]` |

Run `clipio stop` and `clipio start` after editing the file.

### Command line

`clipio help` lists every command. The most useful ones:

```bash
clipio start            # start Clipio in the background
clipio toggle           # open or close the panel
clipio pause            # stop recording (clipio resume to continue)
clipio retention 7      # keep items for 7 days and clean up now
clipio autostart on     # start at login (off to undo)
clipio status           # running state, item count and database path
clipio stop             # quit Clipio
```

### Run from source

```bash
git clone https://github.com/ardazeybek/clipio.git
cd clipio
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[test]"
clipio run                         # runs in this terminal; Ctrl+C stops it
```

## How it works

| Part | Role |
| --- | --- |
| `clipio/core/` | Classifies items, stores them in SQLite and applies the limits. No operating-system code. |
| `clipio/system/` | One small backend per platform: clipboard, paste keystroke, global shortcut, start at login. |
| `clipio/app.py` | The running app: watches the clipboard, shows the panel, answers `clipio` commands over a local socket. |
| `clipio/ui/` | The panel, written in QML (Qt Quick). |

[MAP.md](MAP.md) describes the full architecture, including which backend each system uses. Each folder has its own `README.md` that explains its files.

The test suite runs on Windows, macOS and Linux with every supported Python version on each push ([tests workflow](https://github.com/ardazeybek/clipio/actions/workflows/ci.yml)).

## Contributing

Bug reports, testing on other desktops, documentation fixes and design ideas are all welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## Support and contact

- **Bugs and feature requests:** [GitHub Issues](https://github.com/ardazeybek/clipio/issues)
- **Other questions:** [quantastudio.dev@gmail.com](mailto:quantastudio.dev@gmail.com)

## License

Clipio is released under the [MIT License](LICENSE).
