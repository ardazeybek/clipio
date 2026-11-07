"""User actions on items: copy to the clipboard, pin, delete, clear, pause, set retention."""
from . import config, db, maintenance, paths


# Put an item back on the clipboard through the given backend (text or image)
def copy(con, clipboard, item_id: int) -> bool:
    row = db.get(con, item_id)
    if not row:
        return False
    if row["kind"] == "image":
        f = paths.image_dir() / row["image_file"]
        if not f.exists():
            return False
        ok = clipboard.write_image(f.read_bytes(), row["mime"] or "image/png")
    else:
        ok = clipboard.write_text(row["text"])
    if ok:
        db.touch(con, item_id)
    return ok


# Pin or unpin an item
def toggle_pin(con, item_id: int) -> None:
    db.toggle_pinned(con, item_id)


# Delete one item
def delete(con, item_id: int) -> None:
    db.delete(con, item_id)


# Delete every unpinned item; return how many were deleted
def clear(con) -> int:
    return db.clear_unpinned(con)


# Pause or resume recording (the pause file exists while paused)
def set_paused(paused: bool) -> None:
    f = paths.pause_file()
    if paused:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch()
    else:
        f.unlink(missing_ok=True)


# Save the retention period (1–365 days) and delete older items right away
def set_retention(con, days: int) -> int:
    days = max(1, min(365, int(days)))
    config.set_int("retention_days", days)
    maintenance.run(con)
    return days
