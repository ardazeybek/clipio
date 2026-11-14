// Data store: reads the backend state, filters it and updates the ListModel by differences so cards animate.
pragma Singleton
import QtQuick
import Clipio

QtObject {
    id: store

    property var all: []            // every item (plain objects)
    readonly property bool canClear: all.some(i => !i.pinned)   // something the trash button would delete
    property real now: Date.now() / 1000
    property bool paused: false
    property int retentionDays: 14
    property int panelKeep: 5          // minutes the closed panel stays loaded
    property int total: 0
    property string tab: "all"      // all | text | image | pinned
    property string folder: ""      // folder filter inside the pinned tab ("" = all pinned)
    property var tags: []           // folder names in use
    property var ignoreApps: []     // apps whose copies are not saved
    property var features: ({})        // feature name -> on/off
    property var shortcuts: ({})       // action -> key sequence, e.g. "Ctrl+E"
    property var defaultShortcuts: ({})
    property int secretMinutes: 5
    property bool ocr: false        // OCR tool installed
    property var queue: []          // items the backend still pastes with `clipio next`
    property var marked: []         // cards picked for a paste queue, in order
    property string query: ""
    readonly property ListModel model: ListModel {}
    readonly property int count: model.count

    property string _last: ""

    onTabChanged: { if (tab !== "pinned") folder = ""; rebuild() }
    onFolderChanged: rebuild()
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
        panelKeep = d.panel_keep_minutes === undefined ? 5 : d.panel_keep_minutes
        total = d.total
        tags = d.tags || []; ignoreApps = d.ignore_apps || []; queue = d.queue || []
        features = d.features || {}; shortcuts = d.shortcuts || {}; defaultShortcuts = d.default_shortcuts || {}
        secretMinutes = d.secret_minutes || 5; ocr = !!d.ocr
        all = d.items.map(i => ({
            cid: i.id, kind: i.kind, hint: i.hint, meta: i.meta, preview: i.preview,
            search: i.search, chars: i.chars, lines: i.lines, image: i.image,
            imgW: i.width, imgH: i.height, size: i.size, pinned: i.pinned,
            source: i.source, used: i.used, tag: i.tag || "", secret: !!i.secret,
            title: i.title || "", rich: i.rich || "", template: !!i.template,
            sig: [i.used, i.pinned, i.tag, i.title].join(":")
        }))
        const ids = new Set(all.map(i => i.cid))
        marked = marked.filter(c => ids.has(c))
        rebuild()
    }

    // True when an item belongs to the current tab
    function _matchTab(it) {
        switch (tab) {
        case "text": return it.kind === "text"
        case "image": return it.kind === "image"
        case "pinned": return it.pinned && (folder === "" || it.tag === folder)
        }
        return true
    }

    // True when an item matches the search text
    // "@app" filters by the app the item was copied from; the rest searches the text
    function _matchQuery(it, q) {
        if (q === "") return true
        const words = q.split(/\s+/)
        const apps = words.filter(w => w.length > 1 && w[0] === "@").map(w => w.slice(1))
        const rest = words.filter(w => w[0] !== "@").join(" ")
        const src = it.source.toLowerCase()
        if (apps.some(a => src.indexOf(a) < 0)) return false
        return rest === "" || it.search.indexOf(rest) >= 0 || src.indexOf(rest) >= 0
            || it.tag.toLowerCase().indexOf(rest) >= 0 || it.title.toLowerCase().indexOf(rest) >= 0
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
    // Paste an item tidied (no tracking parameters, no extra whitespace)
    function activateClean(cid) { Backend.activateClean(cid) }
    // Add a card to the paste queue or take it out
    function toggleMark(cid) {
        marked = marked.indexOf(cid) >= 0 ? marked.filter(c => c !== cid) : marked.concat([cid])
    }
    // Position of a card in the paste queue (1-based, 0 = not queued)
    function markNo(cid) { return marked.indexOf(cid) + 1 }
    // Paste the marked cards one after another
    function startQueue() { const ids = marked; marked = []; Backend.startQueue(ids) }
    // Forget the queue (marked cards and the backend's remaining items)
    function clearQueue() { marked = []; Backend.clearQueue() }
    // Put an item in a folder
    function setTag(cid, tag) { Backend.setTag(cid, tag) }
    // Turn an on/off setting on or off
    function setSwitch(key, on) { Backend.setSwitch(key, on) }
    // Stop or start saving copies from an app
    function setAppIgnored(app, ignored) { Backend.setAppIgnored(app, ignored) }
    // True when a feature is on (unknown features count as on)
    function on(name) { return features[name] !== false }
    // Turn a feature on or off (shown at once, saved by the backend)
    function toggleFeature(name) {
        const f = Object.assign({}, features); f[name] = !on(name); features = f
        Backend.setSwitch(name, f[name])
    }
    // Change one shortcut ('' = default)
    function setShortcut(action, keys) {
        const m = Object.assign({}, shortcuts); m[action] = keys || defaultShortcuts[action]; shortcuts = m
        Backend.setShortcut(action, keys)
    }
    // Put all shortcuts back to their defaults
    function resetShortcuts() { shortcuts = Object.assign({}, defaultShortcuts); Backend.resetShortcuts() }

    // Key names for keys that have no printable text
    readonly property var _keyNames: ({
        [Qt.Key_Return]: "Return", [Qt.Key_Enter]: "Return", [Qt.Key_Space]: "Space",
        [Qt.Key_Tab]: "Tab", [Qt.Key_Backtab]: "Backtab", [Qt.Key_Delete]: "Delete",
        [Qt.Key_Backspace]: "Backspace", [Qt.Key_Insert]: "Insert", [Qt.Key_Home]: "Home",
        [Qt.Key_End]: "End", [Qt.Key_Menu]: "Menu", [Qt.Key_F1]: "F1", [Qt.Key_F2]: "F2",
        [Qt.Key_F3]: "F3", [Qt.Key_F4]: "F4", [Qt.Key_F5]: "F5", [Qt.Key_F6]: "F6",
        [Qt.Key_F7]: "F7", [Qt.Key_F8]: "F8", [Qt.Key_F9]: "F9", [Qt.Key_F10]: "F10",
        [Qt.Key_F11]: "F11", [Qt.Key_F12]: "F12"
    })

    // Key sequence text of a key event, e.g. "Ctrl+Shift+E" ("" for a lone modifier)
    function keySeq(e) {
        const k = e.key
        if ([Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_AltGr].indexOf(k) >= 0) return ""
        let name = _keyNames[k]
        if (name === undefined && k >= 0x21 && k <= 0x7e) name = String.fromCharCode(k).toUpperCase()
        if (name === undefined) return ""
        const m = []
        if (e.modifiers & Qt.ControlModifier) m.push("Ctrl")
        if (e.modifiers & Qt.AltModifier) m.push("Alt")
        if (e.modifiers & Qt.ShiftModifier) m.push("Shift")
        if (e.modifiers & Qt.MetaModifier) m.push("Meta")
        return m.concat([name]).join("+")
    }

    // Action bound to a key event ("" when none)
    function actionFor(e) {
        const seq = keySeq(e)
        if (seq === "") return ""
        for (const a in shortcuts) if (shortcuts[a] === seq) return a
        return ""
    }

    // Shortcut of an action as keycaps text, e.g. "Ctrl + E"
    function keysOf(action) { return (shortcuts[action] || defaultShortcuts[action] || "").split("+").join(" + ") }

    // Item by cid (null when gone)
    function find(cid) { return all.find(i => i.cid === cid) || null }
    // Pin or unpin an item (shown at once, saved by the backend)
    function togglePin(cid) { togglePinLocal(cid); Backend.togglePin(cid) }
    // Delete an item
    function remove(cid) { removeLocal(cid); Backend.remove(cid) }
    // Delete every unpinned item
    function clearAll() { all = all.filter(i => i.pinned); rebuild(); Backend.clearAll() }
    // Change how many days items are kept
    function setRetention(d) { retentionDays = d; Backend.setRetention(d) }
    // Change how long the closed panel stays loaded (minutes)
    function setPanelKeep(m) { panelKeep = m; Backend.setPanelKeep(m) }
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

    // The other notation of a color: #hex -> rgb(), rgb() -> #hex
    function colorAlt(s) {
        const c = cssColor(s)
        if (c === "transparent") return ""
        const q = Qt.color(c)
        const h = v => ("0" + Math.round(v * 255).toString(16)).slice(-2).toUpperCase()
        return (s || "").trim()[0] === "#"
            ? "rgb(" + [q.r, q.g, q.b].map(v => Math.round(v * 255)).join(", ") + ")"
            : "#" + h(q.r) + h(q.g) + h(q.b)
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
        // a channel is 0-255 or a percentage; alpha is 0-1 or a percentage
        const ch = v => v.endsWith("%") ? parseFloat(v) / 100 : parseFloat(v) / 255
        const al = v => v === undefined ? 1 : v.endsWith("%") ? parseFloat(v) / 100 : parseFloat(v)
        if ((m = s.match(/^rgba?\(\s*([\d.]+%?)[,\s]+([\d.]+%?)[,\s]+([\d.]+%?)(?:[,\s/]+([\d.]+%?))?/)))
            return Qt.rgba(ch(m[1]), ch(m[2]), ch(m[3]), al(m[4]))
        if ((m = s.match(/^hsla?\(\s*([\d.]+)(?:deg)?[,\s]+([\d.]+)%[,\s]+([\d.]+)%(?:[,\s/]+([\d.]+%?))?/)))
            return Qt.hsla((m[1] % 360) / 360, m[2] / 100, m[3] / 100, al(m[4]))
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
