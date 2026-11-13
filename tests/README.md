# tests/
pytest suite. Runs headless (`QT_QPA_PLATFORM=offscreen`) with temporary data, config and IPC names, so it never touches a real Clipio.

- `conftest.py` — shared fixtures: isolated folders, database connection, fake clipboard, one `QApplication`
- `test_core.py` — classification, paths per OS, settings, storage, skip rules, limits, state export
- `test_cli.py` — the `clipio` command for database-only commands and bad usage
- `test_system.py` — desktop detection, hotkey parsing, paste commands, autostart, Qt clipboard, IPC (waiting and fire-and-forget), panel link, memory trim; Windows- and macOS-only checks run on those systems
- `test_ui.py` — loads the real QML panel and drives it through the service and panel controllers, failing on any QML warning
- `test_e2e.py` — starts a real service process and checks that the panel process starts on demand and quits when closed
