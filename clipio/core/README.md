# clipio/core/
Platform-independent clipboard history logic. Nothing here talks to the operating system's clipboard directly.

- `paths.py` — data, image and config locations for Windows, macOS and Linux
- `config.py` — reads `config.toml`, merges defaults, updates one value (`set_int`)
- `classify.py` — guesses a text's kind (color, link, email, code)
- `db.py` — SQLite storage: add, list, pin, delete, expiry and limits
- `ingest.py` — `Snapshot` type and saving a snapshot as a text or image item
- `export.py` — builds the state the panel shows
- `maintenance.py` — applies the retention rules
- `actions.py` — user actions: copy, pin, delete, clear, pause, retention
