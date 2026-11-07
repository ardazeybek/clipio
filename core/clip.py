"""wl-clipboard ve Hyprland ile konuşur: panoyu okur, yazar, aktif pencereyi sorar, Ctrl+V gönderir."""
import json
import subprocess

TEXT_TYPES = ("text/plain;charset=utf-8", "text/plain", "UTF8_STRING", "STRING", "TEXT")
TERMINALS = {
    "kitty", "alacritty", "foot", "footclient", "wezterm", "org.wezfurlong.wezterm",
    "com.mitchellh.ghostty", "ghostty", "konsole", "org.kde.konsole", "xterm", "urxvt",
    "gnome-terminal-server", "org.gnome.terminal", "tilix", "terminator", "st-256color",
    "org.kde.yakuake", "xfce4-terminal", "lxterminal", "cool-retro-term", "contour",
}


# Komutu çalıştır, çıktıyı bayt olarak döndür (hata olursa None)
def _run(cmd: list[str], data: bytes | None = None, timeout: float = 5):
    try:
        r = subprocess.run(cmd, input=data, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


# Panodaki MIME türlerini listele (pano boşsa boş liste)
def list_types() -> list[str]:
    out = _run(["wl-paste", "--list-types"])
    return out.decode(errors="replace").split() if out else []


# Panodan verilen türde ham veriyi oku
def read(mime: str) -> bytes | None:
    return _run(["wl-paste", "--no-newline", "--type", mime], timeout=10)


# Metni panoya yaz (wl-copy kendini arka plana alır)
def copy_text(text: str) -> bool:
    return _run(["wl-copy", "--type", "text/plain;charset=utf-8"], text.encode()) is not None


# Resim dosyasını panoya yaz
def copy_image(data: bytes, mime: str) -> bool:
    return _run(["wl-copy", "--type", mime], data) is not None


# Panoyu boşalt
def clear() -> None:
    _run(["wl-copy", "--clear"])


# Aktif pencerenin sınıf adını döndür (bilinmiyorsa boş)
def active_class() -> str:
    out = _run(["hyprctl", "-j", "activewindow"], timeout=2)
    try:
        return json.loads(out).get("class", "") if out else ""
    except json.JSONDecodeError:
        return ""


# Aktif pencereye Ctrl+V (terminalde Ctrl+Shift+V) gönder
def send_paste() -> None:
    mods = "CTRL SHIFT" if active_class().lower() in TERMINALS else "CTRL"
    lua = f'hl.dsp.send_shortcut({{mods="{mods}", key="V", window="activewindow"}})'
    out = _run(["hyprctl", "dispatch", lua], timeout=2)
    if out is None or b"error" in out.lower():
        legacy = f"{mods.replace(' ', ',')},V,activewindow"
        _run(["hyprctl", "dispatch", "sendshortcut", legacy], timeout=2)
