"""Öğe üzerinde kullanıcı eylemleri: panoya kopyala, yapıştır, sabitle, sil, duraklat."""
import time
from pathlib import Path

from . import clip, db, export, paths


# Öğenin içeriğini panoya yaz (metin ya da resim)
def copy(con, item_id: int) -> bool:
    row = db.get(con, item_id)
    if not row:
        return False
    if row["kind"] == "image":
        data = (Path(paths.IMAGE_DIR) / row["image_file"]).read_bytes()
        ok = clip.copy_image(data, row["mime"])
    else:
        ok = clip.copy_text(row["text"])
    if ok:
        db.touch(con, item_id)
        export.write_state(con)
    return ok


# Öğeyi panoya yazıp aktif pencereye yapıştır
def paste(con, item_id: int) -> bool:
    if not copy(con, item_id):
        return False
    time.sleep(0.14)   # arayüz kapanıp odak hedef pencereye dönsün
    clip.send_paste()
    return True


# Sabitlemeyi değiştir ve durumu yenile
def toggle_pin(con, item_id: int) -> None:
    db.toggle_pinned(con, item_id)
    export.write_state(con)


# Öğeyi sil ve durumu yenile
def delete(con, item_id: int) -> None:
    db.delete(con, item_id)
    export.write_state(con)


# Sabitlenmemiş her şeyi sil ve durumu yenile
def clear(con) -> int:
    n = db.clear_unpinned(con)
    export.write_state(con)
    return n


# Kaydı duraklat ya da sürdür (paused dosyası var/yok)
def set_paused(con, paused: bool) -> None:
    if paused:
        paths.PAUSE_FILE.touch()
    else:
        paths.PAUSE_FILE.unlink(missing_ok=True)
    export.write_state(con)
