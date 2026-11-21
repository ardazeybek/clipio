<p align="center">
  <img src="docs/assets/contrib-ways.png" width="880" alt="Contributing You do not need to write code to help. Each of these makes Clipio better for everyone. Report a bug. What you did, what you expected, what happened. Test your system. Windows, macOS and less common Linux desktops are extra welcome. Fix the docs. An unclear step in a README? A one-line fix helps. Design and access. Contrast, sizes, keyboard use and animations. With a bug report, tell us: your system and version, your Linux desktop (for example Hyprland, GNOME on Wayland, KDE on X11), and the output of the two commands below." />
</p>

```bash
clipio version
python --version
```

<p align="center">
  <img src="docs/assets/contrib-flow.png" width="880" alt="Workflow From idea to merged in six steps. 1. Look first. Search the open issues. Maybe someone is on it. 2. Talk first. A bigger change? Open an issue with your idea before you start. 3. Fork and branch. For example fix/paste-in-terminal. 4. Make the change. Small and focused beats big and mixed. 5. Run the checks. The tests, then the flow by hand: copy, open, search, paste, pin, delete. 6. Open a pull request. Say what changed and why. Add a screenshot for visual changes." />
</p>

## Run it from source

```bash
git clone https://github.com/<your-username>/clipio.git
cd clipio
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[test]"
clipio run                         # errors and QML warnings show here; Ctrl+C stops it
```

Keep your own history out of the way while you work:

```bash
export CLIPIO_DATA_DIR=/tmp/clipio-dev/data CLIPIO_CONFIG_DIR=/tmp/clipio-dev/config CLIPIO_IPC_NAME=clipio-dev
```

<p align="center">
  <img src="docs/assets/contrib-checks.png" width="880" alt="Checks Green on three systems before it ships. No screen needed. Tests run headless and load the real QML panel. Zero QML warnings. Any warning fails the test. Keep the log clean. Every system. CI runs Windows, macOS and Linux, Python 3.10 to 3.14. Tests that need one system (Windows registry, macOS helpers) are skipped on the others. A pull request passes all of them." />
</p>

```bash
python -m pytest -v
```

<p align="center">
  <img src="docs/assets/contrib-rules.png" width="880" alt="Code style Six rules that keep Clipio easy to read. One job per folder. Its README.md lists every file in one line. Update it with your change. Keep the map true. Update MAP.md when the main flow, a backend or a location changes. Say what it does. A one-line comment on top of every file and every small function. English everywhere. Code, comments, interface texts and docs. Core stays pure. clipio/core/ never touches the OS. That goes in clipio/system/. Theme in one place. Colors, fonts, sizes from Theme.qml , texts from Strings.qml. By contributing, you agree your work is released under the MIT License." />
</p>
