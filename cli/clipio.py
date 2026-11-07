"""Clipio komut satırı: servisi/arayüzü başlatır, öğeler üzerinde eylem yapar (UI de bunu çağırır)."""
import json
import os
import shutil
import signal
import subprocess
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from core import actions, config, db, export, maintenance, paths  # noqa: E402

QS = shutil.which("quickshell") or shutil.which("qs") or "quickshell"
UI_NAME = "clipio"

USAGE = """clipio <komut>
  start            servisi ve arayüzü başlat
  stop             ikisini de durdur
  toggle|show|hide paneli aç/kapat
  paste <id>       öğeyi aktif pencereye yapıştır
  copy <id>        öğeyi panoya al
  pin <id>         sabitle / kaldır
  delete <id>      öğeyi sil
  clear            sabitlenmemişleri sil
  pause|resume     kaydı duraklat / sürdür
  purge            süresi dolanları şimdi temizle
  retention <gün>  saklama süresini ayarla (1-365) ve hemen uygula
  list             öğeleri listele
  status           durum özeti
"""


# Verilen komutu bağımsız (arka plan) süreç olarak başlat
def _spawn(cmd: list[str]) -> None:
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


# Arka plan servisini (clipiod) başlat
def start_daemon() -> None:
    _spawn([sys.executable, os.path.join(ROOT, "daemon", "clipiod.py")])


# Quickshell arayüzünü başlat
def start_ui() -> None:
    _spawn([QS, "-c", UI_NAME, "-d", "-n"])


# Arayüze IPC ile komut gönder; başarılıysa True
def _ipc(fn: str) -> bool:
    r = subprocess.run([QS, "ipc", "-c", UI_NAME, "call", "clipio", fn],
                       capture_output=True, timeout=5)
    return r.returncode == 0


# Arayüz kapalıysa açıp komutu tekrar dene
def ui_call(fn: str) -> None:
    if _ipc(fn):
        return
    start_ui()
    for _ in range(40):
        time.sleep(0.15)
        if _ipc(fn):
            return
    print("Arayüz başlatılamadı (quickshell kurulu mu?)", file=sys.stderr)


# Servis ve arayüzü durdur
def stop_all() -> None:
    subprocess.run([QS, "kill", "-c", UI_NAME], capture_output=True)
    try:
        os.kill(int(paths.PID_FILE.read_text()), signal.SIGTERM)
    except (OSError, ValueError):
        pass


# Öğeleri tek satır halinde yazdır
def list_items(con) -> None:
    for r in db.list_items(con, 50):
        label = (r["text"] or f"[resim {r['width']}x{r['height']}]").replace("\n", " ")[:70]
        print(f"{r['id']:>5} {'*' if r['pinned'] else ' '} {r['kind']:<5} {label}")


# Durum özetini yazdır
def status(con) -> None:
    cfg = config.load()
    total = con.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    print(json.dumps({"items": total, "paused": paths.PAUSE_FILE.exists(),
                      "retention_days": cfg["retention_days"], "db": str(paths.DB_FILE)}))


# arayüze giden komutların IPC fonksiyon adı karşılıkları
UI_COMMANDS = {"toggle": "toggle", "show": "open", "hide": "close"}

# Saklama süresini (gün) kaydet ve hemen uygula
def set_retention(con, days: int) -> None:
    config.set_int("retention_days", max(1, min(365, days)))
    maintenance.run(con)


# id isteyen komutlar
ID_COMMANDS = {"paste": actions.paste, "copy": actions.copy,
               "pin": actions.toggle_pin, "delete": actions.delete}


# Komutu çalıştır
def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd = argv[0]
    if cmd == "start":
        start_daemon(); start_ui()
    elif cmd == "stop":
        stop_all()
    elif cmd in UI_COMMANDS:
        ui_call(UI_COMMANDS[cmd])
    else:
        return _db_command(cmd, argv[1:])
    return 0


# Veritabanı gerektiren komutları çalıştır
def _db_command(cmd: str, args: list[str]) -> int:
    con = db.connect()
    if cmd in ID_COMMANDS and args:
        ID_COMMANDS[cmd](con, int(args[0]))
    elif cmd == "clear":
        actions.clear(con)
    elif cmd in ("pause", "resume"):
        actions.set_paused(con, cmd == "pause")
    elif cmd == "purge":
        maintenance.run(con)
    elif cmd == "retention" and args:
        set_retention(con, int(args[0]))
    elif cmd == "list":
        list_items(con)
    elif cmd == "status":
        status(con)
    else:
        print(USAGE)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
