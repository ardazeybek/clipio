// Arayüz metinleri: Türkçe ve İngilizce sözlük (dil Store.lang'dan gelir).
pragma Singleton
import QtQuick
import Quickshell

Singleton {
    readonly property var tr: ({
        all: "Tümü", text: "Metin", image: "Resim", pinned: "Sabit",
        search: "Ara…", paused: "Kayıt durdu",
        empty: "Henüz bir şey yok", emptySub: "Bir şey kopyala, burada belirsin.",
        noMatch: "Bulunamadı",
        clearTitle: "Her şey silinsin mi?", clearSub: "Kopyaladığın tüm öğeler silinecek. Sabitlediklerin kalır.",
        cancel: "Vazgeç", clearYes: "Evet, sil",
        settings: "Ayarlar", keepFor: "Kopyaladıkların ne kadar saklansın?", days: "%1 gün",
        keepNote: "Bundan eski olanlar silinir. Sabitlenenler hiç silinmez.", done: "Tamam",
        now: "şimdi", min: "dk", hour: "sa", day: "g"
    })
    readonly property var en: ({
        all: "All", text: "Text", image: "Images", pinned: "Pinned",
        search: "Search…", paused: "Paused",
        empty: "Nothing here yet", emptySub: "Copy something and it shows up here.",
        noMatch: "No matches",
        clearTitle: "Clear everything?", clearSub: "All copied items will be deleted. Pinned ones stay.",
        cancel: "Cancel", clearYes: "Yes, delete",
        settings: "Settings", keepFor: "How long should copies be kept?", days: "%1 days",
        keepNote: "Older items are deleted. Pinned items are never deleted.", done: "Done",
        now: "now", min: "m", hour: "h", day: "d"
    })

    // Anahtara göre geçerli dildeki metni döndür; %1 yerine arg koy
    function t(key, arg) {
        const d = Store.lang === "tr" ? tr : en
        const s = d[key] !== undefined ? d[key] : (en[key] !== undefined ? en[key] : key)
        return arg === undefined ? s : s.replace("%1", arg)
    }
}
