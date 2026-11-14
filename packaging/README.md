# packaging/
Builds the ready-to-install app (no Python needed on the user's computer). The release workflow (`.github/workflows/release.yml`) runs this on every `v*` tag and attaches the files to the GitHub release.

- `clipio.spec` — PyInstaller recipe: one `Clipio-Setup` file on Windows and Linux (app files + onedir launcher in `payload/`), `Clipio.app` on macOS; drops unused Qt parts and GTK-theme system libraries
- `entry.py` — entry point of the packaged executable (`clipio.cli.main`; no arguments = setup or open the panel)
- `make_icon.py` — renders the logo SVG to `build/icon.png` (PyInstaller turns it into .ico / .icns)
- The release also carries `SHA256SUMS`; the app's updater (`clipio/system/updater.py`) refuses a download that does not match it
- `install.sh` — one-line Linux install: downloads the latest setup file and runs it

Build locally: `pip install . pyinstaller pillow certifi && python packaging/make_icon.py && pyinstaller packaging/clipio.spec`
