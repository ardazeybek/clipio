"""Clipio'ın disk üzerindeki tüm konumları (veri, resimler, durum dosyası, ayar)."""
import os
from pathlib import Path


# XDG değişkenini oku, yoksa varsayılan klasörü döndür
def _xdg(env: str, fallback: str) -> Path:
    return Path(os.environ.get(env) or Path.home() / fallback)


DATA_DIR = _xdg("XDG_DATA_HOME", ".local/share") / "clipio"
CONFIG_DIR = _xdg("XDG_CONFIG_HOME", ".config") / "clipio"
RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp")

DB_FILE = DATA_DIR / "clipio.db"
IMAGE_DIR = DATA_DIR / "images"
STATE_FILE = DATA_DIR / "state.json"       # arayüzün okuduğu anlık görüntü
PAUSE_FILE = DATA_DIR / "paused"           # varsa kayıt duraklatılmıştır
CONFIG_FILE = CONFIG_DIR / "config.toml"
PID_FILE = RUNTIME_DIR / "clipiod.pid"


# Gerekli klasörleri oluştur
def ensure_dirs() -> None:
    for d in (DATA_DIR, IMAGE_DIR, CONFIG_DIR):
        d.mkdir(parents=True, exist_ok=True)
