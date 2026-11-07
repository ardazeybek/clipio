// Data store: reads the backend state, filters it and updates the ListModel by differences so cards animate.
pragma Singleton
import QtQuick
import Clipio

QtObject {
    id: store

    property var all: []            // every item (plain objects)
    property real now: Date.now() / 1000
    property bool paused: false
    property int retentionDays: 14
    property int total: 0
    property string tab: "all"      // all | text | image | pinned
    property string query: ""
    readonly property ListModel model: ListModel {}
    readonly property int count: model.count

    property string _last: ""

    onTabChanged: rebuild()
    onQueryChanged: rebuild()

    // Ask the backend for fresh state (when the panel opens)
    function reload() { Backend.refresh() }

    // Parse the state JSON and apply the filters
    function parse(txt) {
        if (txt === _last) return
        let d
        try { d = JSON.parse(txt) } catch (e) { return }
        if (!d || !d.items) return     // no state yet
        _last = txt
        now = d.now; paused = d.paused; retentionDays = d.retention_days
        total = d.total
        all = d.items.map(i => ({
            cid: i.id, kind: i.kind, hint: i.hint, meta: i.meta, preview: i.preview,
            search: i.search, chars: i.chars, lines: i.lines, image: i.image,
            imgW: i.width, imgH: i.height, size: i.size, pinned: i.pinned,
            source: i.source, used: i.used, sig: i.used + ":" + i.pinned
        }))
        rebuild()
    }

    // True when an item belongs to the current tab
    function _matchTab(it) {
        switch (tab) {
        case "text": return it.kind === "text"
        case "image": return it.kind === "image"
        case "pinned": return it.pinned
        }
        return true
    }

    // True when an item matches the search text
    function _matchQuery(it, q) {
        return q === "" || it.search.indexOf(q) >= 0 || it.source.toLowerCase().indexOf(q) >= 0
    }

    // Compute the filtered list and apply it to the model
    function rebuild() {
        const q = query.trim().toLowerCase()
        sync(all.filter(it => _matchTab(it) && _matchQuery(it, q)))
    }

    // Match the model to the target list: remove, insert and move rows
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

    // Find cid in the model starting at `from`
    function _indexOf(cid, from) {
        for (let k = from; k < model.count; k++) if (model.get(k).cid === cid) return k
        return -1
    }

    // Show a deletion at once (without waiting for the backend)
    function removeLocal(cid) {
        all = all.filter(i => i.cid !== cid)
        rebuild()
    }

    // Show a pin change at once
    function togglePinLocal(cid) {
        all = all.map(i => i.cid === cid ? Object.assign({}, i, { pinned: !i.pinned, sig: i.used + ":" + !i.pinned }) : i)
        all.sort((a, b) => (b.pinned - a.pinned) || (b.used - a.used))
        rebuild()
    }

    // Paste an item into the previous app, or only copy it
    function activate(cid, doPaste) { Backend.activate(cid, doPaste) }
    // Pin or unpin an item (shown at once, saved by the backend)
    function togglePin(cid) { togglePinLocal(cid); Backend.togglePin(cid) }
    // Delete an item
    function remove(cid) { removeLocal(cid); Backend.remove(cid) }
    // Delete every unpinned item
    function clearAll() { all = all.filter(i => i.pinned); rebuild(); Backend.clearAll() }
    // Change how many days items are kept
    function setRetention(d) { retentionDays = d; Backend.setRetention(d) }
    // Pause or resume recording
    function togglePause() { paused = !paused; Backend.setPaused(paused) }

    // Short relative time text, e.g. "5 m"
    function ago(ts) {
        const s = Math.max(0, now - ts)
        if (s < 45) return Strings.t("now")
        if (s < 3600) return Math.round(s / 60) + " " + Strings.t("min")
        if (s < 86400) return Math.floor(s / 3600) + " " + Strings.t("hour")
        return Math.floor(s / 86400) + " " + Strings.t("day")
    }

    // Short app name from a window class (org.telegram.desktop -> Telegram)
    function appName(cls) {
        if (!cls) return ""
        const generic = ["desktop", "app", "client", "gtk", "qt", "stable"]
        const p = cls.split(".")
        while (p.length > 1 && generic.indexOf(p[p.length - 1].toLowerCase()) >= 0) p.pop()
        const n = p[p.length - 1]
        return n.charAt(0).toUpperCase() + n.slice(1, 18)
    }

    // Human-readable byte size
    function fmtSize(b) {
        return b > 1048576 ? (b / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " KB"
    }

    // Turn a CSS color string into a QML color (#RRGGBBAA, rgb(), hsl())
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

    // Clock: keeps relative times fresh
    property Timer clock: Timer { interval: 20000; running: true; repeat: true; onTriggered: store.now = Date.now() / 1000 }

    // Follow the state the backend publishes
    property Connections backend: Connections {
        target: Backend
        function onStateChanged() { store.parse(Backend.stateJson) }
    }

    Component.onCompleted: parse(Backend.stateJson)
}
