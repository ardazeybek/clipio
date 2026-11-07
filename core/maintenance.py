"""Bakım işleri: süresi dolanları ve sınırı aşanları temizler, state.json'ı yeniler."""
from . import config, db, export


# Tüm saklama kurallarını uygula
def run(con, cfg: dict | None = None) -> None:
    cfg = cfg or config.load()
    db.purge_expired(con, cfg["retention_days"])
    db.trim_count(con, cfg["max_items"])
    db.trim_image_bytes(con, cfg["max_images_total_mb"] * 1024 * 1024)
    export.write_state(con)
