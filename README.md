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
  <p><a href="#quick-start">Quick start</a> · <a href="#usage">Usage</a> · <a href="CONTRIBUTING.md">Contribute</a> · <a href="https://github.com/ardazeybek/clipio/discussions">Discussions</a> · <a href="mailto:quantastudio.dev@gmail.com">Contact</a></p>
</div>

<p align="center">
  <img src="docs/assets/demo.gif" alt="Clipio opening, moving through the cards with the arrow keys, searching for git and for a color, then showing the settings page" width="456" />
</p>

<p align="center"><em>The real Clipio panel with sample data: open it, move with the arrow keys, type to search, change settings.</em></p>

## What is Clipio?

Clipio keeps a history of what you copy. Press the shortcut, pick an earlier item, and Clipio pastes it into the window you were using.

It is made for people who copy the same things again and again and want a simple, good-looking way to get them back. Everything stays on your computer in a local SQLite database. Unpinned items are deleted automatically after the number of days you choose.

Clipio runs on **Windows 10/11, macOS and Linux** (X11 and Wayland). It is written in Python with a Qt Quick interface through PySide6.

### Light on memory

A clipboard history has to keep running to notice what you copy, so Clipio is split in two:

| Part | When it runs | Memory |
| --- | --- | --- |
| **Recorder** — watches the clipboard, saves items, pastes, hotkey, tray | always, in the background | about 25 MB of its own on Linux (≈ 85 MB counting the Python and Qt libraries it shares) |
| **Panel** — the window you see | only while you use it, plus 5 minutes after you close it | freed completely when it quits |

Before 0.3 the whole app, window included, stayed loaded all the time (≈ 420 MB on Linux). Now the panel quits on its own once you stop using it, and the first open after that takes about a second. You choose the trade-off under *Settings → Storage → Keep the panel ready after closing*: free at once, 1, 5 or 30 minutes, or always.

## Features

- **One-shortcut history** — Open the panel, choose an item and it is pasted into the app you were using.
- **Readable cards** — Links, colors, code and images each get their own card, so you can recognise an item at a glance.
- **Search and tabs** — Type to filter, or switch between All, Text, Images and Pinned.
- **Pins that stay** — Pin the things you reuse. Pinned items are never deleted automatically or by *Clear*.
- **Automatic cleanup** — Choose how long items are kept (1, 3, 7, 14 or 30 days) in the settings window.
- **Privacy controls** — Pause recording at any time, list apps whose copies are never saved, and copies that password managers mark as secret are skipped. Password manager apps are always skipped.
- **Secrets hide themselves** — Passwords, API keys, tokens and card numbers are shown as dots and deleted after a few minutes.
- **Clean links** — Tracking parameters (`utm_…`, `fbclid`, `gclid`…) are removed from copied links. *Paste cleaned* also tidies spaces.
- **Paste queue** — Mark several cards and paste them one after another.
- **Card menu** — Right-click a card to edit it before pasting, convert it (UPPER/lower case, JSON, Base64, URL, HEX ↔ RGB), put it in a folder, read text from an image (OCR, needs `tesseract`) or stop saving copies from its app.
- **Folders and templates** — Pinned items can live in folders. Pinned snippets with `{date}`, `{time}`, `{datetime}`, `{weekday}` or `{clipboard}` are filled in when pasted.
- **Small in the background** — Only a light recorder stays running; the panel frees its memory when you are done (see [Light on memory](#light-on-memory)).
- **Smart cards** — Colors show both notations, code is colored, links can show their page title, and every card shows the app it came from. Type `@firefox` to filter by app.

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
| <kbd>Shift</kbd> + <kbd>Enter</kbd> | Paste it cleaned (no tracking, tidy spaces) |
| <kbd>Ctrl</kbd> + <kbd>C</kbd> | Copy it without pasting |
| right click · <kbd>Ctrl</kbd> + <kbd>M</kbd> | Card menu (edit, convert, folder, OCR…) |
| <kbd>Ctrl</kbd> + <kbd>E</kbd> | Edit, then paste |
| <kbd>Ctrl</kbd> + click · <kbd>Ctrl</kbd> + <kbd>Space</kbd> | Add to the paste queue; <kbd>Enter</kbd> pastes the first, `clipio next` the rest |
| <kbd>Alt</kbd> + <kbd>1</kbd>–<kbd>9</kbd> | Paste one of the first nine items (hold <kbd>Alt</kbd> to see the numbers) |
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
| `clean_links` | Remove tracking parameters from copied links | `true` |
| `secret_minutes` | Minutes before copied passwords, keys and card numbers are deleted | `5` |
| `link_titles` | Fetch page titles of copied links (sends a request to the site) | `false` |
| `panel_keep_minutes` | Minutes the closed panel stays loaded before it frees its memory (`0` = at once, `1440` = always ready) | `5` |

Most settings can be changed in the panel instead: the gear button (or <kbd>Ctrl</kbd> + <kbd>,</kbd>) opens a settings page with an animated **How to** guide, **Shortcuts** (click a key and press the new one), **Features** (switch each feature on or off) and **Storage**. Shortcuts are saved as `key_paste`, `key_edit`… and features as `clean_links`, `detect_secrets`, `templates`, `code_colors`, `show_source`, `quick_numbers`, `link_titles`.

Run `clipio stop` and `clipio start` after editing the file.

### Command line

`clipio help` lists every command. The most useful ones:

```bash
clipio start            # start Clipio in the background
clipio toggle           # open or close the panel
clipio next             # paste the next item of the paste queue (bind it to a key)
clipio pause            # stop recording (clipio resume to continue)
clipio retention 7      # keep items for 7 days and clean up now
clipio autostart on     # start at login (off to undo)
clipio status           # running state, whether the panel is loaded, item count, database path
clipio stop             # quit Clipio
```

### Run from source

```bash
git clone https://github.com/ardazeybek/clipio.git
cd clipio
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[test]"
clipio run                         # runs the service in this terminal; Ctrl+C stops it
```

## How it works

| Part | Role |
| --- | --- |
| `clipio/core/` | Classifies items, stores them in SQLite and applies the limits. No operating-system code. |
| `clipio/system/` | One small backend per platform: clipboard, paste keystroke, global shortcut, start at login. |
| `clipio/app.py` | The background service: watches the clipboard, pastes, answers `clipio` commands over a local socket. |
| `clipio/panel.py` | The panel process: started when you open the panel, quits by itself when unused. |
| `clipio/ui/` | The panel, written in QML (Qt Quick). |

[MAP.md](MAP.md) describes the full architecture, including which backend each system uses. Each folder has its own `README.md` that explains its files.

<p align="center">
  <img src="docs/assets/settings.png" alt="The Clipio settings page on the Storage tab: how long copies are kept and how long the closed panel stays ready" width="400" />
</p>

The test suite runs on Windows, macOS and Linux with every supported Python version on each push, including an end-to-end test that starts the real service and panel processes ([tests workflow](https://github.com/ardazeybek/clipio/actions/workflows/ci.yml)).

## Contributing

Bug reports, testing on other desktops, documentation fixes and design ideas are all welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## Support and contact

- **Bugs and feature requests:** [GitHub Issues](https://github.com/ardazeybek/clipio/issues)
- **Other questions:** [quantastudio.dev@gmail.com](mailto:quantastudio.dev@gmail.com)

## License

Clipio is released under the [MIT License](LICENSE).

---

<p align="center">If Clipio saves you time, a star on GitHub helps other people find it.</p>
