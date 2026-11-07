# tests/
pytest suite. Runs headless (`QT_QPA_PLATFORM=offscreen`) with temporary data, config and IPC names, so it never touches a real Clipio.

- `conftest.py` — shared fixtures: isolated folders, database connection, fake clipboard, one `QApplication`
- `test_core.py` — classification, paths per OS, settings, storage, skip rules, limits, state export
- `test_cli.py` — the `clipio` command for database-only commands and bad usage
- `test_system.py` — desktop detection, hotkey parsing, paste commands, autostart, Qt clipboard, IPC; Windows- and macOS-only checks run on those systems
- `test_ui.py` — loads the real QML panel and drives it through the controller, failing on any QML warning
