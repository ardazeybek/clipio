# Clipio — mimari haritası
Hyprland üzerinde Super+V ile açılan, kağıt temalı, tatlı pano geçmişi (eski adları: Sincap, Klip).

## Klasörler
- `install.sh` — komutu, Quickshell bağlantısını, masaüstü girdisini ve simgeyi kurar
- `docs/assets/` — README görselleri
- `core/` — veritabanı, pano erişimi, sınıflandırma, bakım, ayarlar (Python)
- `daemon/` — `clipiod.py`: panoyu izleyen arka plan servisi
- `cli/` — `clipio.py`: komut satırı; arayüzü açar/kapatır, öğe eylemleri
- `ui/` — Quickshell (QML) arayüzü; `components/` içinde panel, kart, tema

## Ana akış
1. `clipiod.py` panoyu izler → `core/ingest.py` sınıflandırır → `core/db.py` SQLite'a yazar → `state.json` anlık görüntüsünü günceller.
2. Super+V → Hyprland `clipio toggle` → `cli/clipio.py` → `qs ipc -c clipio call clipio toggle` → `ui/shell.qml`.
3. `ui/components/Store.qml` `state.json`'u okur; seçim/yapıştırma `clipio paste|copy <id>` ile CLI'ye döner.
4. Ayarlar penceresi saklama süresini `clipio retention <gün>` ile yazar → `core/config.py` config.toml'u günceller → `core/maintenance.py` eskileri hemen siler.

## Dış bağlantılar
- Kısayol: Hyprland ayarında `exec-once = clipio start` ve `SUPER+V → clipio toggle` (layer namespace `clipio`); `install.sh` eklenecek satırları yazdırır
- Veri: `~/.local/share/clipio/` (clipio.db, images/, state.json) · Ayar: `~/.config/clipio/config.toml`
- Quickshell yapılandırması: `~/.config/quickshell/clipio` → `ui/` (symlink) · Komut: `~/.local/bin/clipio`
- Masaüstü girdisi ve ikon: `~/.local/share/applications/clipio.desktop`, `~/.local/share/icons/hicolor/scalable/apps/clipio-paper.svg` (masaüstü girdisi `Icon=clipio-paper`; ad, başlatıcı önbelleğini atlatmak için değişti)

## Tasarım
Sade kağıt teması: eski defter kağıdı zemin, not kağıdı kartlar, altta kağıt yığını gölgesi, hardal bant süsleri. Vurgu şeftali `accent`, sabitler adaçayı `sage` bandı (`ui/components/Theme.qml`). Logo `ui/assets/clipio.svg` (panel başlığı, boş liste ve uygulama simgesi), alt bilgi/kısayol satırı yok; kartta yalnızca içerik ve zaman görünür. Arka perde yok; panel her açılışta ekranın ortasında başlar, boş yerinden sürüklenir, dışına tıklayınca kapanır. Temizleme onayı ve ayarlar panel içi kağıt pencerelerde (`Dialog.qml`). Animasyonlar: açılışta bant düşüp yapışır, kartlar sırayla girer ve seçilince yığından kalkar, sekme yazısı zıplar, butonlar tıklanınca zıplar, dişli üzerine gelince döner. Blur yok.
