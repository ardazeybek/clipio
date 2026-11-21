<div align="center">
  <img src="clipio/ui/assets/clipio.svg" alt="Clipio logo" width="104" />
  <h1>Clipio</h1>
  <p><strong>Copy now. Paste it any time later.</strong></p>
  <p>
    <a href="https://github.com/ardazeybek/clipio/releases/latest"><img src="https://img.shields.io/github/v/release/ardazeybek/clipio?color=E58F6F&label=version" alt="Latest version" /></a>
    <a href="https://github.com/ardazeybek/clipio/actions/workflows/ci.yml"><img src="https://github.com/ardazeybek/clipio/actions/workflows/ci.yml/badge.svg" alt="Test status" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-9CC3A6" alt="MIT license" /></a>
    <img src="https://img.shields.io/badge/price-free-F3D9A4" alt="Free" />
  </p>
  <p><a href="https://ardazeybek.github.io/clipio/"><img src="docs/assets/download-button.svg" alt="Download Clipio" height="56" /></a></p>
</div>

<p align="center">
  <img src="docs/assets/demo.gif" alt="The real Clipio panel: it opens, moves through the cards with the arrow keys, searches for git and for a color, then shows the settings page." width="456" />
</p>

## ✨ Why Clipio

<p align="center">
  <img src="docs/assets/highlights.png" width="880" alt="Why Clipio Copy now. Paste it any time later. Clipio quietly keeps everything you copy. One shortcut brings it all back. One shortcut. Pick a card and it is pasted where you were typing. Calm to look at. A soft paper theme, not another gray box. Private. Your history never leaves your computer. Passwords hide themselves. Light. About 25 MB in the background. The panel loads on demand. Updates itself. New versions install quietly while the panel is closed. Everywhere. Windows, macOS and Linux, X11 and Wayland." />
</p>

<p align="center">
  <img src="docs/assets/how.png" width="880" alt="How it works Three moves. No new habits. 1. Ctrl C. Copy as usual. Clipio keeps every copy. 2. Ctrl Shift V. Press the shortcut. Type to search, or pick a card. 3. It is pasted. Right where you were typing." />
</p>

## 💻 Works on

<p align="center">
  <a href="https://github.com/ardazeybek/clipio/releases/latest/download/Clipio-Setup.exe"><img src="docs/assets/os-windows.png" width="280" alt="Windows. Windows 10 and 11. Opens with Ctrl Shift V. Download.exe." /></a>
  <a href="https://ardazeybek.github.io/clipio/"><img src="docs/assets/os-macos.png" width="280" alt="macOS. Apple Silicon and Intel. Opens with ⌘ ⇧ V. Download.dmg." /></a>
  <a href="https://ardazeybek.github.io/clipio/"><img src="docs/assets/os-linux.png" width="280" alt="Linux. X11 and Wayland. Opens with Super V or your key. Download." /></a>
</p>

## 🌟 Features

<p align="center">
  <img src="docs/assets/features-everyday.png" width="880" alt="Everyday Fast for the things you do all day. Quick paste. Enter or a click pastes it where you were. Search and tabs. Type to find. All, Text, Images and Pinned. Pins and folders. Pinned items never expire. Sort them into folders. Alt + 1…9. Paste one of the first nine cards in one move. Paste queue. Mark a few cards, then paste them one by one. Edit, then paste. Fix a typo before it lands. Ctrl + E." />
</p>

<p align="center">
  <img src="docs/assets/features-smart.png" width="880" alt="Smart cards Every card knows what it holds. Colors. A swatch, plus HEX and RGB. Code. Colored like in your editor. Clean links. Tracking junk removed. Page titles if you want them. Images. Thumbnails, and text read from images (OCR). Source app. Each card shows where it came from. @app filters. Templates. {date}, {time} and {clipboard} filled in when pasted." />
</p>

<p align="center">
  <img src="docs/assets/features-privacy.png" width="880" alt="Privacy Your clipboard stays yours. Secrets hide themselves. Passwords, keys and card numbers vanish after 5 minutes. Ignored apps. Password managers are always skipped. Add your own. Pause. Stop recording with one click. Auto clean-up. Old items go after 1 to 30 days. You choose. Local only. Everything sits in one small database on your own disk. Nothing sent. No telemetry, no account. Link titles stay off unless you turn them on." />
</p>

## 📥 Install

<p align="center">
  <a href="https://ardazeybek.github.io/clipio/"><img src="docs/assets/install.png" width="880" alt="Install Ready in under a minute. 1. Download. Download. The page picks your system. 2. Install. Press Install. No Python. No admin rights. 3. Done. Clipio starts now and with your computer." /></a>
</p>

<p align="center">
  <img src="docs/assets/first-run.png" width="880" alt="First time only One extra click, then never again. Clipio is new and not yet signed, so your system asks once. Windows. Blue SmartScreen box? Click More info , then Run anyway. macOS. Right-click Clipio, then Open. Allow it in Privacy &amp; Security → Accessibility. Linux. Open Clipio-Setup-Linux , or paste the one-line command below." />
</p>

Linux in one line:

```bash
curl -fsSL https://github.com/ardazeybek/clipio/releases/latest/download/install.sh | sh
```

Developers can install with Python 3.10–3.14 (Linux also needs `wl-clipboard` or `xdotool`):

```bash
pipx install git+https://github.com/ardazeybek/clipio.git
clipio start
clipio autostart on
```

## 🔄 Updates

<p align="center">
  <img src="docs/assets/updates.png" width="880" alt="Updates Always the newest. Zero effort. Updates itself. 1 Looks for a new version at start and once a day. 2 Downloads it and checks it against a checksum. 3 Installs while the panel is closed. History and settings stay. 4 A small note says “Clipio was updated”. Turn it off in Settings → Features → Automatic updates. Installed with Python? You just get a note. Leaves cleanly. Windows Settings → Apps → Clipio → Uninstall. macOS and Linux Run clipio uninstall. Your history and settings are kept, in case you come back." />
</p>

## ⌨️ Shortcuts

<p align="center">
  <img src="docs/assets/shortcuts.png" width="880" alt="Shortcuts Your hands never leave the keyboard. Change any of them in Settings → Shortcuts. Click outside the panel to close it. ↑ ↓ PgUp PgDn. Move. Enter or click. Paste. Shift Enter. Paste cleaned · no tracking, tidy spaces. Ctrl C. Copy only. Ctrl E. Edit, then paste. Ctrl M or right-click. Card menu. Ctrl P. Pin or unpin. Ctrl Space or Ctrl + click. Add to the paste queue. Alt 1…9. Paste one of the first nine. Del. Delete. Tab Shift Tab. Next or previous tab. Esc. Clear the search, then close. Ctrl ,. Settings." />
</p>

## ⚙️ Settings

<p align="center">
  <img src="docs/assets/settings-tabs.png" width="880" alt="Settings Make it yours in four tabs. Open them with the gear button or Ctrl ,. How to. A small animated guide for every feature. Shortcuts. Click a key, press the new one. Done. Features. Switch each one on or off. Storage. How long items stay, how long the panel stays ready, which apps to skip." />
</p>

<p align="center">
  <img src="docs/assets/config.png" width="880" alt="Settings file Prefer a text file? Here it is. Edit config.toml , then run clipio stop and clipio start. Windows. Settings %APPDATA%\clipio\config.toml History %LOCALAPPDATA%\clipio\. macOS. Both in ~/Library/Application Support/clipio/. Linux. Settings ~/. config/clipio/config.toml History ~/. local/share/clipio/. retention_days Days before unpinned items are deleted 14. max_items Most items to keep 500. max_text_kb · max_image_mb Bigger texts and images are not saved 1024 · 25. max_images_total_mb Total space for images 1024. persist Put the last copy back if an app empties the clipboard true. hotkey Global shortcut, like &quot;ctrl+alt+v&quot; per system. ignore_apps Apps never recorded, like [&quot;KeePassXC&quot;] []. clean_links Remove tracking bits from links true. secret_minutes Minutes before secrets are deleted 5. link_titles Fetch page titles (visits the site) false. auto_update Install new versions by itself true. panel_keep_minutes Minutes the closed panel stays ready (0 = free now) 5." />
</p>

## 🐧 Linux Wayland

<p align="center">
  <img src="docs/assets/wayland.png" width="880" alt="Linux Wayland Wayland? Pick your own key. Wayland does not let apps grab global shortcuts. So you bind clipio toggle to a key once. Bind a key. Hyprland and Sway : add one line to your config (below). GNOME and KDE : Settings → Keyboard → Custom shortcut, with the command clipio toggle. Pasting works on. ✓ Hyprland out of the box. ✓ Sway and wlroots with wtype, the installer gets it. ~ GNOME Clipio copies, you press Ctrl + V." />
</p>

```ini
# hyprland.conf
bind = SUPER, V, exec, clipio toggle
```

```ini
# sway config
bindsym $mod+v exec clipio toggle
```

## 🍎 macOS

<p align="center">
  <img src="docs/assets/macos.png" width="880" alt="macOS Two yeses, asked once. Allow Clipio under System Settings → Privacy &amp; Security. Accessibility. So Clipio can paste into other apps. Without it, picking a card copies it and you press ⌘ V. Input Monitoring. So the global shortcut ⌘ ⇧ V works in every app." />
</p>

## 🖥️ Command line

```bash
clipio toggle           # open or close the panel
clipio next             # paste the next item of the paste queue
clipio pause            # stop recording (clipio resume to continue)
clipio retention 7      # keep items for 7 days
clipio update           # look for a new version now
clipio status           # is it running, how many items
clipio start / stop     # start or quit Clipio
clipio uninstall        # remove the app (history stays)
clipio help             # everything else
```

## ❓ FAQ

<p align="center">
  <img src="docs/assets/faq.png" width="880" alt="FAQ Questions people ask. No Does it send my clipboard anywhere?. Never. It stays in a local database. Only the update check talks to GitHub. Safe What about passwords?. Password managers are skipped. Copied passwords, keys and card numbers are hidden and deleted after 5 minutes. No Will it slow my computer down?. The recorder uses about 25 MB. The panel frees its memory a few minutes after you close it. Once Why does Windows warn me?. Clipio is new and not signed yet. Click More info, then Run anyway. Only the first time. Yes Does it work on Wayland?. Yes. Bind clipio toggle to a key. On GNOME it copies and you paste. Free What does it cost?. Nothing. MIT license. No account, no ads, no trial." />
</p>

## 🛠️ For developers

<p align="center">
  <img src="docs/assets/dev.png" width="880" alt="For developers Two small processes. Nothing hidden. Python and Qt Quick (QML) through PySide6. Needs Python 3.10 to 3.14. The recorder. always on · ≈ 25 MB of its own. Clipboard, saving, pasting, hotkey, tray and updates. The panel. only while you use it, plus 5 min. The window you see. It quits by itself and gives all its memory back. clipio/core/ Sorts and stores items in SQLite. No OS code. clipio/system/ One small backend per system: clipboard, paste, hotkey, autostart, updates. clipio/setup/ The installer of the ready-made app. clipio/ui/ The panel and setup windows in QML. packaging/ Builds the installers on every release. Tests run on Windows, macOS and Linux with Python 3.10 to 3.14 on every push. MAP.md maps the whole thing." />
</p>

```bash
git clone https://github.com/ardazeybek/clipio.git && cd clipio
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[test]"
clipio run                                          # Ctrl+C stops it
```

## 🤝 Contributing

<p align="center">
  <a href="CONTRIBUTING.md"><img src="docs/assets/contribute.png" width="880" alt="Contribute Help Clipio get better. You do not need to write code. Every small report helps. 1. Report a bug. What you did, what you expected, what happened. 2. Test your desktop. Windows, macOS, a rare Linux desktop? Tell us what breaks. 3. Polish the details. Clearer docs, better contrast, a kinder animation. Read the contributing guide →." /></a>
</p>

## 💬 Support

<p align="center">
  <a href="https://github.com/ardazeybek/clipio/issues"><img src="docs/assets/support-issues.png" width="280" alt="Found a bug?. Open a GitHub Issue →." /></a>
  <a href="https://github.com/ardazeybek/clipio/discussions"><img src="docs/assets/support-discussions.png" width="280" alt="Ideas and questions. GitHub Discussions →." /></a>
  <a href="mailto:quantastudio.dev@gmail.com"><img src="docs/assets/support-mail.png" width="280" alt="Anything else. Send an email →." /></a>
</p>

## 📜 License

<p align="center">
  <a href="LICENSE"><img src="docs/assets/license.png" width="880" alt="MIT license Free. Yours to keep. ✓ Use it, change it, share it. ✓ No account, no ads, no trial. ✓ Free today and later. © 2026 Arda Zeybek · MIT License. Did Clipio save you a few copies?. A star helps other people find it. Press ★ Star at the top of this page. Star at the top ↑." /></a>
</p>
