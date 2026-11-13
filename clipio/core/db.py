"""SQLite storage: adds, lists, pins and deletes clipboard items and removes expired ones."""
import sqlite3
import time

from . import paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT NOT NULL,            -- text | image
    hash       TEXT NOT NULL UNIQUE,
    text       TEXT,
    hint       TEXT NOT NULL DEFAULT 'text',   -- text|url|color|email|code
    meta       TEXT NOT NULL DEFAULT '',
    image_file TEXT,
    mime       TEXT,
    width      INTEGER NOT NULL DEFAULT 0,
    height     INTEGER NOT NULL DEFAULT 0,
    size       INTEGER NOT NULL DEFAULT 0,
    pinned     INTEGER NOT NULL DEFAULT 0,
    source     TEXT NOT NULL DEFAULT '',
    created    REAL NOT NULL,
    used       REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_used ON items(used);
"""

# Columns added after the first release: name -> definition (added to old databases on connect)
EXTRA_COLUMNS = {
    "tag": "TEXT NOT NULL DEFAULT ''",        # folder name for pinned items
    "secret": "INTEGER NOT NULL DEFAULT 0",   # 1 when the text looks like a password or key
    "title": "TEXT NOT NULL DEFAULT ''",      # page title of a link
}


# Connect to the database and create the schema
def connect() -> sqlite3.Connection:
    paths.ensure_dirs()
    con = sqlite3.connect(paths.db_file(), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    _migrate(con)
    return con


# Add columns that older databases do not have yet
def _migrate(con: sqlite3.Connection) -> None:
    have = {r["name"] for r in con.execute("PRAGMA table_info(items)")}
    for name, definition in EXTRA_COLUMNS.items():
        if name not in have:
            con.execute(f"ALTER TABLE items ADD COLUMN {name} {definition}")
    con.commit()


# Refresh the "last used" time if the same content exists, otherwise insert a new row
def upsert(con: sqlite3.Connection, **f) -> int:
    now = time.time()
    row = con.execute("SELECT id FROM items WHERE hash=?", (f["hash"],)).fetchone()
    if row:
        con.execute("UPDATE items SET used=?, source=? WHERE id=?",
                    (now, f.get("source", ""), row["id"]))
        con.commit()
        return row["id"]
    cols = ", ".join(f) + ", created, used"
    marks = ", ".join("?" for _ in f) + ", ?, ?"
    cur = con.execute(f"INSERT INTO items ({cols}) VALUES ({marks})", (*f.values(), now, now))
    con.commit()
    return cur.lastrowid


# Return one item by id
def get(con: sqlite3.Connection, item_id: int):
    return con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()


# Return the most recently used item
def latest(con: sqlite3.Connection):
    return con.execute("SELECT * FROM items ORDER BY used DESC LIMIT 1").fetchone()


# Panel order: pinned items first, then the most recently used
def list_items(con: sqlite3.Connection, limit: int = 300) -> list:
    return con.execute(
        "SELECT * FROM items ORDER BY pinned DESC, used DESC LIMIT ?", (limit,)
    ).fetchall()


# Pin or unpin an item
def set_pinned(con: sqlite3.Connection, item_id: int, pinned: bool) -> None:
    con.execute("UPDATE items SET pinned=? WHERE id=?", (int(pinned), item_id))
    con.commit()


# Flip the pinned state
def toggle_pinned(con: sqlite3.Connection, item_id: int) -> None:
    con.execute("UPDATE items SET pinned = 1 - pinned WHERE id=?", (item_id,))
    con.commit()


# Delete an image file from disk when no other row uses it
def _drop_image_file(con: sqlite3.Connection, image_file: str | None) -> None:
    if not image_file:
        return
    still = con.execute("SELECT 1 FROM items WHERE image_file=?", (image_file,)).fetchone()
    if not still:
        (paths.image_dir() / image_file).unlink(missing_ok=True)


# Delete the given rows and their image files
def _delete_rows(con: sqlite3.Connection, rows: list) -> int:
    for r in rows:
        con.execute("DELETE FROM items WHERE id=?", (r["id"],))
    con.commit()
    for r in rows:
        _drop_image_file(con, r["image_file"])
    return len(rows)


# Delete one item
def delete(con: sqlite3.Connection, item_id: int) -> int:
    rows = con.execute("SELECT id, image_file FROM items WHERE id=?", (item_id,)).fetchall()
    return _delete_rows(con, rows)


# Delete everything that is not pinned
def clear_unpinned(con: sqlite3.Connection) -> int:
    rows = con.execute("SELECT id, image_file FROM items WHERE pinned=0").fetchall()
    return _delete_rows(con, rows)


# Delete unpinned items older than the retention period
def purge_expired(con: sqlite3.Connection, retention_days: float) -> int:
    cutoff = time.time() - retention_days * 86400
    rows = con.execute(
        "SELECT id, image_file FROM items WHERE pinned=0 AND used<?", (cutoff,)
    ).fetchall()
    return _delete_rows(con, rows)


# Delete the oldest unpinned items above the item limit
def trim_count(con: sqlite3.Connection, max_items: int) -> int:
    rows = con.execute(
        "SELECT id, image_file FROM items WHERE pinned=0 ORDER BY used DESC LIMIT -1 OFFSET ?",
        (max_items,),
    ).fetchall()
    return _delete_rows(con, rows)


# Delete the oldest images once their total size passes the limit
def trim_image_bytes(con: sqlite3.Connection, max_bytes: int) -> int:
    rows = con.execute(
        "SELECT id, image_file, size FROM items WHERE kind='image' AND pinned=0 ORDER BY used DESC"
    ).fetchall()
    total, doomed = 0, []
    for r in rows:
        total += r["size"]
        if total > max_bytes:
            doomed.append(r)
    return _delete_rows(con, doomed)


# Remove image files on disk that the database no longer knows
def sweep_orphan_images(con: sqlite3.Connection) -> None:
    known = {r[0] for r in con.execute("SELECT image_file FROM items WHERE image_file IS NOT NULL")}
    for f in paths.image_dir().glob("*"):
        if f.name not in known:
            f.unlink(missing_ok=True)


# Mark an item as used now (moves it to the top of the list)
def touch(con: sqlite3.Connection, item_id: int) -> None:
    con.execute("UPDATE items SET used=? WHERE id=?", (time.time(), item_id))
    con.commit()


# Put an item in a folder ('' removes it); a folder also pins the item
def set_tag(con: sqlite3.Connection, item_id: int, tag: str) -> None:
    tag = tag.strip()[:40]
    con.execute("UPDATE items SET tag=?, pinned=CASE WHEN ?<>'' THEN 1 ELSE pinned END WHERE id=?",
                (tag, tag, item_id))
    con.commit()


# Folder names in use, A-Z
def tags(con: sqlite3.Connection) -> list[str]:
    rows = con.execute("SELECT DISTINCT tag FROM items WHERE tag<>'' ORDER BY tag COLLATE NOCASE")
    return [r[0] for r in rows]


# Save a link's page title
def set_title(con: sqlite3.Connection, item_id: int, title: str) -> None:
    con.execute("UPDATE items SET title=? WHERE id=?", (title[:200], item_id))
    con.commit()


# Delete unpinned secret items older than the given minutes
def purge_secrets(con: sqlite3.Connection, minutes: float) -> int:
    cutoff = time.time() - minutes * 60
    rows = con.execute(
        "SELECT id, image_file FROM items WHERE secret=1 AND pinned=0 AND created<?", (cutoff,)
    ).fetchall()
    return _delete_rows(con, rows)
