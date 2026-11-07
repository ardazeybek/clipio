# core/
Clipio iş mantığı (arayüzden bağımsız).

- `paths.py` — veri, ayar ve pid dosyası konumları
- `config.py` — config.toml okuma, varsayılanlar, tek ayarı yazma (`set_int`)
- `classify.py` — metin türü tahmini (renk, bağlantı, e-posta, kod)
- `db.py` — SQLite: ekle, sorgula, sabitle, sil, süre dolumu, sınırlar
- `clip.py` — wl-clipboard ve Hyprland ile konuşma (oku, yaz, Ctrl+V gönder)
- `ingest.py` — panodaki içeriği seçip veritabanına kaydetme
- `export.py` — arayüzün okuduğu `state.json` üretimi
- `maintenance.py` — saklama kurallarını uygulama ve state yenileme
- `actions.py` — kullanıcı eylemleri: kopyala, yapıştır, sabitle, sil, duraklat
