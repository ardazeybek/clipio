"""Housekeeping: deletes expired items and items over the size and count limits."""
from . import config, db


# Apply every retention rule
def run(con, cfg: dict | None = None) -> None:
    cfg = cfg or config.load()
    db.purge_expired(con, cfg["retention_days"])
    db.trim_count(con, cfg["max_items"])
    db.trim_image_bytes(con, cfg["max_images_total_mb"] * 1024 * 1024)
