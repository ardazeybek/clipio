// Veri deposu: state.json'ı okur, filtreler ve ListModel'i animasyonlu eklemeler için farklarıyla günceller.
pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: store

    property var all: []            // tüm öğeler (düz nesneler)
    property real now: Date.now() / 1000
    property bool paused: false
    property int retentionDays: 14
    property int total: 0
    property string lang: "en"
    property string tab: "all"      // all | text | image | pinned
    property string query: ""
    readonly property ListModel model: ListModel {}
    readonly property int count: model.count

    readonly property string home: Quickshell.env("HOME")
    readonly property string dataDir: (Quickshell.env("XDG_DATA_HOME") || home + "/.local/share") + "/clipio"
    readonly property string bin: Quickshell.env("CLIPIO_BIN") || home + "/.local/bin/clipio"
    property string _last: ""

    onTabChanged: rebuild()
    onQueryChanged: rebuild()

    // Dosyayı yeniden oku (pano değişince ve panel açılınca)
    function reload() { file.reload() }

    // state.json metnini çözümle ve filtreleri uygula
    function parse(txt) {
        if (txt === _last) return
        let d
        try { d = JSON.parse(txt) } catch (e) { return }
        _last = txt
        now = d.now; paused = d.paused; retentionDays = d.retention_days
        lang = d.lang; total = d.total
        all = d.items.map(i => ({
            cid: i.id, kind: i.kind, hint: i.hint, meta: i.meta, preview: i.preview,
            search: i.search, chars: i.chars, lines: i.lines, image: i.image,
            imgW: i.width, imgH: i.height, size: i.size, pinned: i.pinned,
            source: i.source, used: i.used, sig: i.used + ":" + i.pinned
        }))
        rebuild()
    }

    // Öğe geçerli sekmeye uyuyor mu
    function _matchTab(it) {
        switch (tab) {
        case "text": return it.kind === "text"
        case "image": return it.kind === "image"
        case "pinned": return it.pinned
        }
        return true
    }

    // Öğe arama sorgusuna uyuyor mu
    function _matchQuery(it, q) {
        return q === "" || it.search.indexOf(q) >= 0 || it.source.toLowerCase().indexOf(q) >= 0
    }

    // Filtrelenmiş hedef listeyi hesapla ve modele uygula
    function rebuild() {
        const q = query.trim().toLowerCase()
        sync(all.filter(it => _matchTab(it) && _matchQuery(it, q)))
    }

    // Modeli hedef listeyle eşitle: silinenleri çıkar, yenileri ekle, sırayı taşı
    function sync(target) {
        const ids = new Set(target.map(t => t.cid))
        for (let i = model.count - 1; i >= 0; i--)
            if (!ids.has(model.get(i).cid)) model.remove(i)
        for (let i = 0; i < target.length; i++) {
            const t = target[i]
            if (i < model.count && model.get(i).cid === t.cid) {
                if (model.get(i).sig !== t.sig) model.set(i, t)
                continue
            }
            const j = _indexOf(t.cid, i + 1)
            if (j >= 0) { model.move(j, i, 1); if (model.get(i).sig !== t.sig) model.set(i, t) }
            else model.insert(i, t)
        }
    }

    // Modelde cid'yi from'dan itibaren ara
    function _indexOf(cid, from) {
        for (let k = from; k < model.count; k++) if (model.get(k).cid === cid) return k
        return -1
    }

    // Silmeyi hemen yansıt (arka plan onayını beklemeden)
    function removeLocal(cid) {
        all = all.filter(i => i.cid !== cid)
        rebuild()
    }

    // Sabitlemeyi hemen yansıt
    function togglePinLocal(cid) {
        all = all.map(i => i.cid === cid ? Object.assign({}, i, { pinned: !i.pinned, sig: i.used + ":" + !i.pinned }) : i)
        all.sort((a, b) => (b.pinned - a.pinned) || (b.used - a.used))
        rebuild()
    }

    // clipio komutunu arka planda çalıştır
    function run(args) { Quickshell.execDetached([bin].concat(args)) }

    // Bir öğeyi yapıştır ya da yalnızca kopyala
    function activate(cid, doPaste) { run([doPaste ? "paste" : "copy", String(cid)]) }
    function togglePin(cid) { togglePinLocal(cid); run(["pin", String(cid)]) }
    function remove(cid) { removeLocal(cid); run(["delete", String(cid)]) }
    function clearAll() { all = all.filter(i => i.pinned); rebuild(); run(["clear"]) }
    function setRetention(d) { retentionDays = d; run(["retention", String(d)]) }
    function togglePause() { paused = !paused; run([paused ? "pause" : "resume"]) }

    // "x önce" biçiminde kısa zaman metni
    function ago(ts) {
        const s = Math.max(0, now - ts)
        if (s < 45) return Strings.t("now")
        if (s < 3600) return Math.round(s / 60) + " " + Strings.t("min")
        if (s < 86400) return Math.floor(s / 3600) + " " + Strings.t("hour")
        return Math.floor(s / 86400) + " " + Strings.t("day")
    }

    // Pencere sınıfından kısa uygulama adı üret (org.telegram.desktop -> Telegram)
    function appName(cls) {
        if (!cls) return ""
        const generic = ["desktop", "app", "client", "gtk", "qt", "stable"]
        const p = cls.split(".")
        while (p.length > 1 && generic.indexOf(p[p.length - 1].toLowerCase()) >= 0) p.pop()
        const n = p[p.length - 1]
        return n.charAt(0).toUpperCase() + n.slice(1, 18)
    }

    // Bayt boyutunu okunur yaz
    function fmtSize(b) {
        return b > 1048576 ? (b / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " KB"
    }

    // CSS renk metnini QML rengine çevir (#RRGGBBAA, rgb(), hsl())
    function cssColor(s) {
        s = (s || "").trim()
        let m
        if (s[0] === "#") {
            let h = s.slice(1)
            if (h.length === 3 || h.length === 4) h = h.split("").map(c => c + c).join("")
            if (h.length === 8) return "#" + h.slice(6) + h.slice(0, 6)
            return "#" + h
        }
        if ((m = s.match(/^rgba?\(\s*([\d.]+)%?[,\s]+([\d.]+)%?[,\s]+([\d.]+)%?(?:[,\s/]+([\d.]+))?/)))
            return Qt.rgba(m[1] / 255, m[2] / 255, m[3] / 255, m[4] === undefined ? 1 : m[4])
        if ((m = s.match(/^hsla?\(\s*([\d.]+)(?:deg)?[,\s]+([\d.]+)%[,\s]+([\d.]+)%(?:[,\s/]+([\d.]+))?/)))
            return Qt.hsla(m[1] / 360, m[2] / 100, m[3] / 100, m[4] === undefined ? 1 : m[4])
        return "transparent"
    }

    // Saat: göreli zamanlar canlı kalsın
    Timer { interval: 20000; running: true; repeat: true; onTriggered: store.now = Date.now() / 1000 }

    FileView {
        id: file
        path: store.dataDir + "/state.json"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: store.parse(text())
    }

    // Dosya izleme kaçırırsa diye panel açıkken periyodik yenile
    Timer { interval: 900; running: store.watching; repeat: true; onTriggered: file.reload() }
    property bool watching: false
}
