"""SQLite deposu: pano öğelerini ekler, sorgular, sabitler, siler ve süresi dolanları temizler."""
import sqlite3
import time
from pathlib import Path

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


# Veritabanına bağlan ve şemayı hazırla
def connect() -> sqlite3.Connection:
    paths.ensure_dirs()
    con = sqlite3.connect(paths.DB_FILE, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


# Aynı içerik varsa "son kullanım" zamanını yenile, yoksa yeni satır ekle
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


# Tek bir öğeyi id ile getir
def get(con: sqlite3.Connection, item_id: int):
    return con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()


# En son kullanılan öğeyi getir
def latest(con: sqlite3.Connection):
    return con.execute("SELECT * FROM items ORDER BY used DESC LIMIT 1").fetchone()


# Arayüz sırası: önce sabitlenenler, sonra en yeni kullanılanlar
def list_items(con: sqlite3.Connection, limit: int = 300) -> list:
    return con.execute(
        "SELECT * FROM items ORDER BY pinned DESC, used DESC LIMIT ?", (limit,)
    ).fetchall()


# Öğeyi sabitle ya da sabitlemeyi kaldır
def set_pinned(con: sqlite3.Connection, item_id: int, pinned: bool) -> None:
    con.execute("UPDATE items SET pinned=? WHERE id=?", (int(pinned), item_id))
    con.commit()


# Sabitleme durumunu tersine çevir
def toggle_pinned(con: sqlite3.Connection, item_id: int) -> None:
    con.execute("UPDATE items SET pinned = 1 - pinned WHERE id=?", (item_id,))
    con.commit()


# Resim dosyasını başka satır kullanmıyorsa diskten sil
def _drop_image_file(con: sqlite3.Connection, image_file: str | None) -> None:
    if not image_file:
        return
    still = con.execute("SELECT 1 FROM items WHERE image_file=?", (image_file,)).fetchone()
    if not still:
        (paths.IMAGE_DIR / image_file).unlink(missing_ok=True)


# Verilen satırları ve resim dosyalarını sil
def _delete_rows(con: sqlite3.Connection, rows: list) -> int:
    for r in rows:
        con.execute("DELETE FROM items WHERE id=?", (r["id"],))
    con.commit()
    for r in rows:
        _drop_image_file(con, r["image_file"])
    return len(rows)


# Tek öğeyi sil
def delete(con: sqlite3.Connection, item_id: int) -> int:
    rows = con.execute("SELECT id, image_file FROM items WHERE id=?", (item_id,)).fetchall()
    return _delete_rows(con, rows)


# Sabitlenmemiş her şeyi sil
def clear_unpinned(con: sqlite3.Connection) -> int:
    rows = con.execute("SELECT id, image_file FROM items WHERE pinned=0").fetchall()
    return _delete_rows(con, rows)


# Saklama süresi dolan (sabitlenmemiş) öğeleri sil
def purge_expired(con: sqlite3.Connection, retention_days: float) -> int:
    cutoff = time.time() - retention_days * 86400
    rows = con.execute(
        "SELECT id, image_file FROM items WHERE pinned=0 AND used<?", (cutoff,)
    ).fetchall()
    return _delete_rows(con, rows)


# Öğe sayısı sınırını aşan en eski sabitlenmemiş öğeleri sil
def trim_count(con: sqlite3.Connection, max_items: int) -> int:
    rows = con.execute(
        "SELECT id, image_file FROM items WHERE pinned=0 ORDER BY used DESC LIMIT -1 OFFSET ?",
        (max_items,),
    ).fetchall()
    return _delete_rows(con, rows)


# Toplam resim boyutu sınırını aşınca en eski resimleri sil
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


# Diskte olup veritabanında olmayan resim dosyalarını temizle
def sweep_orphan_images(con: sqlite3.Connection) -> None:
    known = {r[0] for r in con.execute("SELECT image_file FROM items WHERE image_file IS NOT NULL")}
    for f in Path(paths.IMAGE_DIR).glob("*"):
        if f.name not in known:
            f.unlink(missing_ok=True)


# Öğeyi "şimdi kullanıldı" olarak işaretle (listede en üste çıkar)
def touch(con: sqlite3.Connection, item_id: int) -> None:
    con.execute("UPDATE items SET used=? WHERE id=?", (time.time(), item_id))
    con.commit()
