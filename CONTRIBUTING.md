# Contributing to Clipio

Thanks for helping. You do not need to write code to contribute. These are all useful:

- **Bug reports** — what you did, what you expected and what happened.
- **Testing** — try Clipio on your system, desktop and apps, and report what breaks. Windows, macOS and less common Linux desktops are especially welcome.
- **Documentation** — fix unclear steps in the README or in a folder's `README.md`.
- **Design and accessibility** — contrast, sizes, keyboard use and animations.

Bugs and ideas go to [GitHub Issues](https://github.com/ardazeybek/clipio/issues). When reporting a bug, include your operating system and version, your desktop on Linux (for example Hyprland, GNOME on Wayland, KDE on X11), and the output of `clipio version` and `python --version`.

## Workflow

1. Look through the existing issues first.
2. For a larger change, open an issue and describe your idea before you start.
3. Fork the repository and create a branch, for example `fix/paste-in-terminal`.
4. Make your change.
5. Run the checks below.
6. Open a pull request that explains what changed and why. Add a screenshot for visual changes.

## Development setup

You need Python 3.10 to 3.14. On Linux Wayland you also need `wl-clipboard`.

```bash
git clone https://github.com/<your-username>/clipio.git
cd clipio
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[test]"
clipio run
```

`clipio run` keeps Clipio in the terminal, so errors and QML warnings are printed there. Stop it with <kbd>Ctrl</kbd> + <kbd>C</kbd> and start it again after a change. To keep your own history out of the way while developing, point Clipio at other folders:

```bash
export CLIPIO_DATA_DIR=/tmp/clipio-dev/data CLIPIO_CONFIG_DIR=/tmp/clipio-dev/config CLIPIO_IPC_NAME=clipio-dev
```

## Checks

```bash
python -m pytest -v
```

The tests run without a screen (`QT_QPA_PLATFORM=offscreen`, set by `tests/conftest.py`). They load the real QML panel and fail on any QML warning. Tests that need a specific system (the Windows registry, macOS helpers) are skipped elsewhere.

GitHub Actions runs the same suite on Windows, macOS and Linux with Python 3.10 to 3.14, plus once with the oldest supported PySide6. A pull request should pass all of them.

Before opening a pull request, also try the flow you changed by hand: copy something, open the panel, then search, paste, pin and delete.

## Code style

- Each folder has one job, and its `README.md` gives a one-line description of every file in it. Update that file when you add, remove or change one.
- [`MAP.md`](MAP.md) is the architecture map. Update it when the main flow, a platform backend or an external location changes.
- Each file starts with a one-line comment or docstring that says what it does.
- Keep functions small and put a one-line comment above each one that says what it does.
- Everything is written in English: code, comments, interface texts and documentation.
- Code in `clipio/core/` must not depend on the operating system. Platform differences go in `clipio/system/`.
- Colors, fonts and sizes come from [`clipio/ui/components/Theme.qml`](clipio/ui/components/Theme.qml), and interface texts from `Strings.qml`. Do not hard-code them in components.

## License

By contributing, you agree that your contributions are released under the [MIT License](LICENSE).
