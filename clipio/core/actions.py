"""User actions on items: copy (plain, clean, templates), edit, convert, folders, pin, delete, clear, pause, settings."""
import hashlib

from . import classify, clean, config, db, maintenance, paths, sensitive, template, transform


# Text that goes on the clipboard for an item: templates filled, optionally cleaned
def text_for_paste(row, clipboard, clean_it: bool = False) -> str:
    text = row["text"] or ""
    if row["pinned"] and template.has_placeholders(text) and config.load()["templates"]:
        before = clipboard.read().text if "{clipboard}" in text else None
        text = template.expand(text, (before or b"").decode("utf-8", "replace"))
    return clean.clean_text(text) if clean_it else text


# Put an item back on the clipboard through the given backend (text or image);
# clean_it pastes the text tidied (no tracking parameters, no extra whitespace)
def copy(con, clipboard, item_id: int, clean_it: bool = False) -> bool:
    row = db.get(con, item_id)
    if not row:
        return False
    if row["kind"] == "image":
        f = paths.image_dir() / row["image_file"]
        if not f.exists():
            db.delete(con, item_id)   # the image file is gone: drop the broken item
            return False
        ok = clipboard.write_image(f.read_bytes(), row["mime"] or "image/png")
    else:
        ok = clipboard.write_text(text_for_paste(row, clipboard, clean_it))
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


# Save how many minutes the closed panel stays loaded (0–1440); return the stored value
def set_panel_keep(minutes: int) -> int:
    minutes = max(0, min(1440, int(minutes)))
    config.set_int("panel_keep_minutes", minutes)
    return minutes


# Save a text as an item made inside Clipio (edits, conversions, OCR); return its id
def save_text(con, text: str, source: str = "Clipio") -> int | None:
    if not text or not text.strip():
        return None
    hint, meta = classify.classify(text)
    raw = text.encode()
    return db.upsert(con, kind="text", hash=hashlib.sha256(raw).hexdigest(), text=text, hint=hint,
                     meta=meta, size=len(raw), source=source, secret=int(sensitive.is_sensitive(text)))


# Convert an item's text and save the result as a new item; return its id
def convert(con, item_id: int, name: str) -> int | None:
    row = db.get(con, item_id)
    if not row or row["kind"] != "text":
        return None
    out = transform.apply(name, row["text"])
    return save_text(con, out, row["source"] or "Clipio") if out else None


# Conversions that work on an item's text
def conversions(con, item_id: int) -> list[str]:
    row = db.get(con, item_id)
    return transform.available(row["text"]) if row and row["kind"] == "text" else []


# Put an item in a folder ('' takes it out)
def set_tag(con, item_id: int, tag: str) -> None:
    db.set_tag(con, item_id, tag)


# Stop saving copies from this app (adds it to ignore_apps)
def ignore_app(app: str) -> list[str]:
    apps = config.load()["ignore_apps"]
    if app and app.lower() not in {a.lower() for a in apps}:
        apps.append(app)
        config.set_value("ignore_apps", apps)
    return apps


# Save copies from this app again
def unignore_app(app: str) -> list[str]:
    apps = [a for a in config.load()["ignore_apps"] if a.lower() != app.lower()]
    config.set_value("ignore_apps", apps)
    return apps


# Turn an on/off setting on or off (only the known switches)
def set_switch(key: str, on: bool) -> None:
    if key in config.FEATURES or key == "persist":
        config.set_value(key, bool(on))


# Change one panel shortcut; '' puts the default back. False for an unknown action
def set_shortcut(action: str, keys: str) -> bool:
    if action not in config.SHORTCUTS:
        return False
    config.set_value(f"key_{action}", keys.strip()[:40] or config.SHORTCUTS[action])
    return True


# Put every panel shortcut back to its default
def reset_shortcuts() -> None:
    for action, keys in config.SHORTCUTS.items():
        config.set_value(f"key_{action}", keys)
