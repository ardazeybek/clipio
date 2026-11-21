# docs/
Documentation and images for the GitHub page.

- `index.html` — the download page (GitHub Pages): detects the visitor's system and links the matching file of the latest release
- `capture.py` — renders the pictures below from the real QML panel with sample data (`python docs/capture.py`, needs ffmpeg for the GIF)
- `assets/download-button.svg` — the drawn download button at the top of the README
- `assets/src/` — one HTML page per README / CONTRIBUTING / CODE_OF_CONDUCT picture in the paper theme (`base.css` shared style, `fit.js` sizes the panel, `icons.js` icons); `render.sh [name]` renders them to `assets/<name>.png` at 2x with headless Chromium
- `assets/*.png` (other than the two below) — those rendered pictures; `social.png` is the 1280x640 social preview
- `assets/overview.png` — panel screenshot (sample data)
- `assets/demo.gif` — short recording: opening, moving, searching and the settings page
- `assets/settings.png` — the settings page (Storage tab), also shown inside `settings-tabs.png`
