# Contributing to Clipio

Thanks for helping. You do not need to write code to contribute. These are all useful:

- **Bug reports** — what you did, what you expected and what happened.
- **Testing** — try Clipio on your Hyprland setup, terminal and apps, and report what breaks.
- **Documentation** — fix unclear steps in the READMEs or in a folder's `README.md`.
- **Translations** — interface texts live in [`ui/components/Strings.qml`](ui/components/Strings.qml) (Turkish and English today).
- **Design and accessibility** — contrast, sizes, keyboard use and animations.

Bugs and ideas go to [GitHub Issues](https://github.com/ardazeybek/clipio/issues). Please include your Hyprland and Quickshell versions (`hyprctl version`, `qs --version`) when reporting a bug.

## Workflow

1. Look through the existing issues first.
2. For a larger change, open an issue and describe your idea before you start.
3. Fork the repository and create a branch, for example `fix/paste-in-terminal`.
4. Make your change.
5. Run the checks below.
6. Open a pull request that explains what changed and why. Add a screenshot for visual changes.

## Development setup

You need Hyprland, Quickshell, `wl-clipboard` and Python 3.11 or newer. Clone your fork and run the installer from it:

```bash
git clone https://github.com/<your-username>/clipio.git
cd clipio
./install.sh
clipio start
```

`~/.config/quickshell/clipio` now points to your `ui/` folder. Quickshell reloads the panel by itself when you save a `.qml` file. Restart the background service after changing Python code:

```bash
clipio stop
clipio start
```

The panel's log shows QML errors and warnings:

```bash
qs log -c clipio
```

## Checks

The project has no automated test suite yet. Before opening a pull request:

- Make sure `qs log -c clipio` shows no new errors or binding-loop warnings after the panel reloads.
- Check that the Python files still compile: `python3 -m py_compile core/*.py cli/*.py daemon/*.py`.
- If you changed `install.sh`, run `bash -n install.sh`.
- Try the flow you changed by hand: copy something, open the panel, then search, paste, pin and delete.

## Code style

- Each folder has one job, and its `README.md` gives a one-line description of every file in it. Update that file when you add, remove or change one.
- [`MAP.md`](MAP.md) is the architecture map. Update it when the main flow or external connections change.
- Each file starts with a one-line comment that says what it does.
- Keep functions small and put a one-line comment above each one that says what it does.
- Comments in the code are written in Turkish; match the surrounding code.
- Colors, fonts and sizes come from [`ui/components/Theme.qml`](ui/components/Theme.qml), and texts from `Strings.qml`. Do not hard-code them in components.

## License

By contributing, you agree that your contributions are released under the [MIT License](LICENSE).
