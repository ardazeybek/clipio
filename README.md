<div align="center">
  <img src="clipio/ui/assets/clipio.svg" alt="Clipio logo" width="104" />
  <h1>Clipio</h1>
  <p><strong>Find and paste anything you copied earlier, with one shortcut.</strong></p>
  <p>A cozy, paper-themed clipboard history that remembers your text, links, colors, code and images.</p>

  <p>
    <img src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4?logo=windows&logoColor=white" alt="Windows 10 and 11" />
    <img src="https://img.shields.io/badge/macOS-Apple%20Silicon%20%7C%20Intel-000000?logo=apple&logoColor=white" alt="macOS on Apple Silicon and Intel" />
    <img src="https://img.shields.io/badge/Linux-X11%20%7C%20Wayland-FCC624?logo=linux&logoColor=black" alt="Linux on X11 and Wayland" />
  </p>
  <p>
    <a href="https://github.com/ardazeybek/clipio/releases/latest"><img src="https://img.shields.io/github/v/release/ardazeybek/clipio?color=E58F6F&label=version" alt="Latest version" /></a>
    <a href="https://github.com/ardazeybek/clipio/actions/workflows/ci.yml"><img src="https://github.com/ardazeybek/clipio/actions/workflows/ci.yml/badge.svg" alt="Test status" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-9CC3A6" alt="MIT license" /></a>
    <img src="https://img.shields.io/badge/price-free-F3D9A4" alt="Free" />
  </p>

  <p>
    <a href="https://ardazeybek.github.io/clipio/"><img src="docs/assets/download-button.svg" alt="Download Clipio" height="56" /></a>
  </p>

  <p>
    <a href="#-features">Features</a> ·
    <a href="#-install">Install</a> ·
    <a href="#%EF%B8%8F-shortcuts">Shortcuts</a> ·
    <a href="#%EF%B8%8F-settings">Settings</a> ·
    <a href="CONTRIBUTING.md">Contribute</a>
  </p>
</div>

<p align="center">
  <img src="docs/assets/demo.gif" alt="Clipio opening, moving through the cards with the arrow keys, searching for git and for a color, then showing the settings page" width="456" />
</p>

<p align="center"><em>The real Clipio panel: open it, move with the arrow keys, type to search, change settings.</em></p>

---

## ✨ Why Clipio?

<p align="center">
  <img src="docs/assets/art/highlights.svg" width="760" alt="One shortcut: pick a copy and it is pasted. Lovely to look at: a calm paper theme. Private: everything stays on your computer. Light: about 25 MB in the background. Updates itself, quietly. Everywhere: Windows, macOS and Linux." />
</p>

## 💻 Works on

<p align="center">
  <a href="https://github.com/ardazeybek/clipio/releases/latest/download/Clipio-Setup.exe"><img src="docs/assets/art/os-windows.svg" width="220" alt="Download for Windows 10 and 11" /></a>
  <a href="https://ardazeybek.github.io/clipio/"><img src="docs/assets/art/os-macos.svg" width="220" alt="Download for macOS, Apple Silicon and Intel" /></a>
  <a href="https://ardazeybek.github.io/clipio/"><img src="docs/assets/art/os-linux.svg" width="220" alt="Download for Linux, X11 and Wayland" /></a>
</p>

| System | Versions | Opens with | Automatic paste |
| :--- | :--- | :---: | :---: |
| **Windows** | 10 and 11 | <kbd>Ctrl</kbd> <kbd>Shift</kbd> <kbd>V</kbd> | Yes |
| **macOS** | Apple Silicon and Intel | <kbd>⌘</kbd> <kbd>⇧</kbd> <kbd>V</kbd> | Yes |
| **Linux X11** | any desktop | <kbd>Super</kbd> <kbd>V</kbd> | Yes |
| **Linux Wayland** | Hyprland, Sway, KDE, GNOME | a key you choose (see *Linux Wayland* below) | Yes (GNOME: copy only) |

## 🌟 Features

<p align="center">
  <img src="docs/assets/art/features-everyday.svg" width="760" alt="Everyday: quick paste with Enter or a click; search and tabs; pins and folders that never expire; Alt + 1 to 9 pastes one of the first nine; a paste queue." />
</p>

<p align="center">
  <img src="docs/assets/art/features-smart.svg" width="760" alt="Smart cards: color swatches with HEX and RGB; colored code; clean links with optional page titles; image thumbnails and OCR (needs tesseract); the source app on each card, @app filters; edit and convert (case, JSON, Base64, URL); templates like {date}, {time}, {clipboard}." />
</p>

<p align="center">
  <img src="docs/assets/art/features-privacy.svg" width="760" alt="Privacy: passwords, keys and card numbers are hidden and deleted after a few minutes; password managers and apps you choose are never recorded; pause with one click; old items are deleted after 1 to 30 days; everything stays in a small local database." />
</p>

## 📥 Install

### The easy way (recommended)

<p align="center">
  <a href="https://ardazeybek.github.io/clipio/"><img src="docs/assets/art/install.svg" width="760" alt="1. Download: the download page picks your system. 2. Open the file and press Install, no Python or admin rights needed. 3. That is it: Clipio starts now and with your computer." /></a>
</p>

| System | File | First time only |
| :--- | :--- | :--- |
| Windows | `Clipio-Setup.exe` | If SmartScreen appears: **More info → Run anyway** |
| macOS | `Clipio-macOS-AppleSilicon.dmg` or `…-Intel.dmg` | Right-click Clipio → **Open**; allow it under *Privacy & Security → Accessibility* |
| Linux | `Clipio-Setup-Linux` | Or paste the command below into a terminal |

```bash
curl -fsSL https://github.com/ardazeybek/clipio/releases/latest/download/install.sh | sh
```

### Updates

Clipio looks for a new version when it starts and once a day. It downloads it, checks it against a checksum, and installs it quietly while the panel is closed. You'll see a small *"Clipio was updated"* note. Turn it off in **Settings → Features → Automatic updates**, or check right away with `clipio update`.

### Uninstall

| System | How |
| :--- | :--- |
| Windows | **Settings → Apps → Clipio → Uninstall** |
| macOS / Linux | run `clipio uninstall` |

Your history and settings are kept, in case you come back.

<details>
<summary><b>Install with Python (for developers)</b></summary>

Needs Python 3.10–3.14. On Linux also `wl-clipboard` (Wayland) or `xdotool` (X11).

```bash
pipx install git+https://github.com/ardazeybek/clipio.git
clipio start
clipio autostart on
```

Python installs don't update themselves; Clipio tells you when a new version is out (`pipx upgrade clipio`).

</details>

## ⌨️ Shortcuts

<p align="center">
  <img src="docs/assets/art/steps.svg" width="760" alt="1. Copy as usual: Clipio keeps every copy. 2. Press the shortcut, then search or pick a card. 3. It is pasted right where you were typing." />
</p>

| Key | Action |
| :--- | :--- |
| <kbd>↑</kbd> <kbd>↓</kbd> · <kbd>PgUp</kbd> <kbd>PgDn</kbd> | Move |
| <kbd>Enter</kbd> · click | Paste |
| <kbd>Shift</kbd> + <kbd>Enter</kbd> | Paste cleaned (no tracking, tidy spaces) |
| <kbd>Ctrl</kbd> + <kbd>C</kbd> | Copy only |
| <kbd>Ctrl</kbd> + <kbd>E</kbd> | Edit, then paste |
| <kbd>Ctrl</kbd> + <kbd>M</kbd> · right click | Card menu |
| <kbd>Ctrl</kbd> + <kbd>P</kbd> | Pin or unpin |
| <kbd>Ctrl</kbd> + <kbd>Space</kbd> · <kbd>Ctrl</kbd> + click | Add to the paste queue |
| <kbd>Alt</kbd> + <kbd>1</kbd>…<kbd>9</kbd> | Paste one of the first nine |
| <kbd>Del</kbd> | Delete |
| <kbd>Tab</kbd> · <kbd>Shift</kbd> + <kbd>Tab</kbd> | Next / previous tab |
| <kbd>Esc</kbd> | Clear the search, then close |
| <kbd>Ctrl</kbd> + <kbd>,</kbd> | Settings |

Every in-panel shortcut can be changed in **Settings → Shortcuts**. Clicking outside the panel closes it.

## ⚙️ Settings

Open them with the gear button or <kbd>Ctrl</kbd> + <kbd>,</kbd>:

<p align="center">
  <img src="docs/assets/art/settings-tabs.svg" width="760" alt="Settings tabs: How to, an animated guide per feature; Shortcuts, click a key and press the new one; Features, switch each one on or off; Storage, how long items are kept, how long the closed panel stays ready and ignored apps." />
</p>

<p align="center">
  <img src="docs/assets/settings.png" alt="The Clipio settings page on the Storage tab" width="400" />
</p>

<details>
<summary><b>Settings file (config.toml)</b></summary>

| System | Settings file | History |
| :--- | :--- | :--- |
| Windows | `%APPDATA%\clipio\config.toml` | `%LOCALAPPDATA%\clipio\` |
| macOS | `~/Library/Application Support/clipio/config.toml` | same folder |
| Linux | `~/.config/clipio/config.toml` | `~/.local/share/clipio/` |

| Setting | What it does | Default |
| :--- | :--- | :--- |
| `retention_days` | Days before unpinned items are deleted | `14` |
| `max_items` | Most items to keep | `500` |
| `max_text_kb` / `max_image_mb` | Larger texts / images are not saved | `1024` / `25` |
| `max_images_total_mb` | Total size limit for images | `1024` |
| `persist` | Put the last item back when the source app empties the clipboard | `true` |
| `hotkey` | Global shortcut, e.g. `"ctrl+alt+v"` | per system |
| `ignore_apps` | Apps never recorded, e.g. `["KeePassXC"]` | `[]` |
| `clean_links` | Remove tracking parameters from links | `true` |
| `secret_minutes` | Minutes before secrets are deleted | `5` |
| `link_titles` | Fetch page titles of links (visits the site) | `false` |
| `auto_update` | Install new versions by itself | `true` |
| `panel_keep_minutes` | Minutes the closed panel stays ready (`0` = free at once, `1440` = always) | `5` |

Run `clipio stop` and `clipio start` after editing the file by hand.

</details>

<details>
<summary><b>Linux Wayland</b></summary>

Wayland doesn't let apps grab global shortcuts, so bind `clipio toggle` to a key yourself:

| Desktop | How |
| :--- | :--- |
| **Hyprland** | `bind = SUPER, V, exec, clipio toggle` in `hyprland.conf` |
| **Sway** | `bindsym $mod+v exec clipio toggle` |
| **GNOME / KDE** | *Settings → Keyboard → Custom shortcut* with the command `clipio toggle` |

Pasting works on Hyprland out of the box and with [`wtype`](https://github.com/atx/wtype) on Sway and other wlroots desktops (the installer fetches it). On GNOME, Clipio copies the item and you paste with <kbd>Ctrl</kbd> + <kbd>V</kbd>.

</details>

<details>
<summary><b>macOS permissions</b></summary>

macOS asks once for:

- **Accessibility** — so Clipio can paste into other apps.
- **Input Monitoring** — for the global shortcut.

Allow Clipio under *System Settings → Privacy & Security*. Without Accessibility, picking an item still copies it and you paste with <kbd>⌘</kbd> + <kbd>V</kbd>.

</details>

<details>
<summary><b>Command line</b></summary>

`clipio help` lists everything. The handy ones:

```bash
clipio toggle           # open or close the panel
clipio next             # paste the next item of the paste queue
clipio pause            # stop recording (clipio resume to continue)
clipio retention 7      # keep items for 7 days
clipio update           # look for a new version now
clipio status           # is it running, how many items
clipio start / stop     # start or quit Clipio
clipio uninstall        # remove the app (history stays)
```

</details>

<details>
<summary><b>How it works (for developers)</b></summary>

Clipio is two small processes written in Python with a Qt Quick (QML) interface through PySide6:

| Part | When it runs | Memory |
| :--- | :--- | :--- |
| **Recorder** — clipboard, saving, pasting, hotkey, tray, updates | always | ≈ 25 MB of its own |
| **Panel** — the window you see | while you use it, plus a few minutes | freed completely when it quits |

| Folder | Role |
| :--- | :--- |
| `clipio/core/` | Classifies and stores items (SQLite), applies limits — no OS code |
| `clipio/system/` | One small backend per platform: clipboard, paste, hotkey, autostart, updates |
| `clipio/setup/` | The installer of the ready-made app |
| `clipio/ui/` | The panel and setup windows in QML |
| `packaging/` | Builds the installers (PyInstaller) on every release |

Run it from source:

```bash
git clone https://github.com/ardazeybek/clipio.git && cd clipio
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[test]"
clipio run                                          # Ctrl+C stops it
```

[MAP.md](MAP.md) maps the whole architecture; every folder has its own `README.md`. The tests run on Windows, macOS and Linux with Python 3.10–3.14 on every push.

</details>

## 🤝 Contributing

Bug reports, testing on other desktops, translations, docs and design ideas are all welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## 💬 Support

<p align="center">
  <a href="https://github.com/ardazeybek/clipio/issues"><img src="docs/assets/art/support-issues.svg" width="240" alt="Bugs and ideas: GitHub Issues" /></a>
  <a href="https://github.com/ardazeybek/clipio/discussions"><img src="docs/assets/art/support-discussions.svg" width="240" alt="Questions: GitHub Discussions" /></a>
  <a href="mailto:quantastudio.dev@gmail.com"><img src="docs/assets/art/support-mail.svg" width="240" alt="Anything else: send an email" /></a>
</p>

## 📜 License

Free and open source under the [MIT License](LICENSE).

---

<p align="center">⭐ If Clipio saves you time, a star on GitHub helps other people find it.</p>
