# clipio/core/
Platform-independent clipboard history logic. Nothing here talks to the operating system's clipboard directly.

- `paths.py` — data, image, lock and config locations for Windows, macOS and Linux
- `config.py` — reads `config.toml`, merges defaults, updates one value (`set_int`); wrong or out-of-range values fall back to safe ones; `panel_keep_minutes` says how long the closed panel stays loaded
- `classify.py` — guesses a text's kind (color, link, email, code)
- `db.py` — SQLite storage: add, list, pin, delete, expiry and limits
- `ingest.py` — `Snapshot` type and saving a snapshot as a text or image item
- `export.py` — builds the state the panel shows
- `maintenance.py` — applies the retention rules
- `actions.py` — user actions: copy, pin, delete, clear, pause, retention, panel memory time (an image item whose file is gone is removed)
- `clean.py` — removes tracking parameters (utm_, fbclid…) from links and tidies whitespace
- `transform.py` — quick conversions for the card menu (case, JSON, Base64, URL, HEX ↔ RGB)
- `sensitive.py` — spots passwords, API keys, tokens, card numbers and IBANs (hidden, deleted after `secret_minutes`)
- `template.py` — fills `{date}`, `{time}`, `{clipboard}`… in pinned snippets when pasted
- `highlight.py` — colors code cards (escaped Qt styled text)
