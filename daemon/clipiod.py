"""Clipio arka plan servisi: panoyu izler, kaydeder, süresi dolanları temizler, panoyu kalıcı tutar."""
import os
import queue
import socket
import signal
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import actions, clip, config, db, export, ingest, maintenance, paths  # noqa: E402

WATCH_CMD = ["wl-paste", "--watch", "sh", "-c", "cat >/dev/null; echo c"]
MAINTENANCE_EVERY = 3600   # saniye


# Çalışan başka bir clipiod varsa True döndür, yoksa pid dosyasını yaz
def _already_running() -> bool:
    try:
        pid = int(paths.PID_FILE.read_text())
        os.kill(pid, 0)
        if "clipiod" in open(f"/proc/{pid}/cmdline").read():
            return True
    except (OSError, ValueError):
        pass
    paths.PID_FILE.write_text(str(os.getpid()))
    return False


_watcher: subprocess.Popen | None = None   # çalışan wl-paste izleyicisi


# wl-paste --watch çıktısını okuyup her değişiklikte kuyruğa olay koy
def _watch_loop(events: queue.Queue, stop: threading.Event) -> None:
    global _watcher
    while not stop.is_set():
        proc = _watcher = subprocess.Popen(WATCH_CMD, stdout=subprocess.PIPE, text=True)
        for _ in proc.stdout:
            events.put("change")
        proc.wait()
        time.sleep(2)   # izleyici düştüyse kısa bekleyip yeniden başlat


# Hyprland olay soketini dinle; pencere kapanınca kuyruğa "window" koy
def _hypr_loop(events: queue.Queue) -> None:
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if not sig:
        return
    path = f"{paths.RUNTIME_DIR}/hypr/{sig}/.socket2.sock"
    while True:
        try:
            with socket.socket(socket.AF_UNIX) as s:
                s.connect(path)
                for line in s.makefile("r", errors="replace"):
                    if line.startswith("closewindow>>"):
                        events.put("window")
        except OSError:
            pass
        time.sleep(3)


# Kaynak uygulama kapanıp pano boşalınca son öğeyi geri yükle
def _restore_if_empty(con, cfg: dict) -> bool:
    if clip.list_types():
        return False
    last = db.latest(con)
    if cfg["persist"] and last:
        actions.copy(con, last["id"])
    return True


# Tek bir pano değişikliğini işle
def handle_change(con) -> None:
    cfg = config.load()
    if _restore_if_empty(con, cfg):
        return
    if ingest.capture(con, cfg) is not None:
        maintenance.run(con, cfg)


# Pencere kapandıktan kısa süre sonra pano boşaldıysa geri yükle
def handle_window_closed(con) -> None:
    time.sleep(0.4)
    _restore_if_empty(con, config.load())


# Aynı anda gelen olayları birleştirip olay türlerinin kümesini döndür
def _drain(first: str, events: queue.Queue) -> set:
    time.sleep(0.06)
    kinds = {first}
    while not events.empty():
        kinds.add(events.get_nowait())
    return kinds


# Servisi temiz kapat: izleyiciyi öldür, pid dosyasını sil
def _shutdown(stop: threading.Event) -> None:
    stop.set()
    if _watcher:
        _watcher.terminate()
    paths.PID_FILE.unlink(missing_ok=True)
    os._exit(0)


# Ana döngü: olay gelince işle, olmazsa saatte bir bakım yap
def main() -> None:
    paths.ensure_dirs()
    config.write_default_if_missing()
    if _already_running():
        return
    con = db.connect()
    maintenance.run(con)
    db.sweep_orphan_images(con)
    events, stop = queue.Queue(), threading.Event()
    threading.Thread(target=_watch_loop, args=(events, stop), daemon=True).start()
    threading.Thread(target=_hypr_loop, args=(events,), daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: _shutdown(stop))
    while True:
        try:
            kinds = _drain(events.get(timeout=MAINTENANCE_EVERY), events)
            if "change" in kinds:
                handle_change(con)
            elif "window" in kinds:
                handle_window_closed(con)
        except queue.Empty:
            maintenance.run(con)


if __name__ == "__main__":
    main()
