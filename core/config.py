"""Kullanıcı ayarlarını (config.toml) varsayılanlarla birleştirip okur."""
import tomllib

from . import paths

DEFAULTS = {
    "retention_days": 14,        # sabitlenmemiş öğeler bu kadar gün sonra silinir
    "max_items": 500,            # saklanacak en fazla öğe sayısı
    "max_text_kb": 1024,         # bundan büyük metinler kaydedilmez
    "max_image_mb": 25,          # bundan büyük resimler kaydedilmez
    "max_images_total_mb": 1024, # tüm resimlerin toplam üst sınırı
    "persist": True,             # kaynak uygulama kapanınca panoyu geri yükle
    "language": "auto",          # auto | tr | en
    "ignore_apps": [],           # kopyalanması kaydedilmeyecek pencere sınıfları
}

TEMPLATE = """# Clipio ayarları
retention_days = 14          # sabitlenmemiş öğeler kaç gün sonra silinsin
max_items = 500              # en fazla kaç öğe saklansın
max_text_kb = 1024           # bundan büyük metinler kaydedilmez
max_image_mb = 25            # bundan büyük resimler kaydedilmez
max_images_total_mb = 1024   # tüm resimlerin toplam sınırı
persist = true               # kaynak uygulama kapanınca panoyu geri yükle
language = "auto"            # auto | tr | en
ignore_apps = []             # örn. ["KeePassXC", "org.keepassxc.KeePassXC"]
"""


# Ayar dosyası yoksa şablondan oluştur
def write_default_if_missing() -> None:
    if not paths.CONFIG_FILE.exists():
        paths.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        paths.CONFIG_FILE.write_text(TEMPLATE, encoding="utf-8")


# Dosyadaki değerleri varsayılanların üstüne yazarak ayarları döndür
def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        with open(paths.CONFIG_FILE, "rb") as f:
            cfg.update(tomllib.load(f))
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        pass
    return cfg


# Bir tam sayı ayarını dosyada güncelle (satır yoksa sona ekle), yorumları korur
def set_int(key: str, value: int) -> None:
    write_default_if_missing()
    lines = paths.CONFIG_FILE.read_text(encoding="utf-8").splitlines()
    new = f"{key} = {int(value)}"
    for i, line in enumerate(lines):
        if line.split("=")[0].strip() == key:
            comment = line[line.index("#"):] if "#" in line else ""
            lines[i] = (new.ljust(29) + comment).rstrip()
            break
    else:
        lines.append(new)
    paths.CONFIG_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
