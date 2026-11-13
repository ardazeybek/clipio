// Looping mini animation that shows one feature: a tiny panel with search, cards, keys, cursor and menu.
// Each kind describes its scene as a function of time t (0..1); the same pieces draw every demo.
import QtQuick

Item {
    id: root
    property string kind: "paste"
    property string keys: ""          // keycaps shown while the shortcut is "pressed"
    property bool playing: visible
    property real t: 0
    readonly property var sc: scene(kind, t)

    implicitHeight: 132
    clip: true

    NumberAnimation on t {
        from: 0; to: 1; duration: 3600
        loops: Animation.Infinite
        running: root.playing
    }

    // 0..1 progress of t between a and b
    function ph(t, a, b) { return Math.max(0, Math.min(1, (t - a) / (b - a))) }
    // Text typed letter by letter between a and b
    function typed(s, t, a, b) { return s.slice(0, Math.round(s.length * ph(t, a, b))) }

    // Scene of one demo at time t: search text, cards, pressed keys, cursor, menu
    function scene(kind, t) {
        const c = (text, o) => Object.assign({ text: text, hi: false, badge: 0, op: 1, tape: false, flash: 0, mono: false, dots: false, chip: "" }, o || {})
        const flashAt = (a) => Math.max(0, 1 - Math.abs(t - a) * 12)
        const s = { query: "", cards: [], keys: "", down: false, cursor: null, menu: [], menuHi: -1 }
        switch (kind) {
        case "paste": {
            const sel = t < 0.25 ? 0 : t < 0.45 ? 1 : 2
            s.cards = [c("Meeting moved to Thursday", { hi: sel === 0 }), c("https://example.com", { hi: sel === 1 }),
                       c("Thanks, see you soon!", { hi: sel === 2, flash: flashAt(0.7), op: 1 - ph(t, 0.75, 0.9) })]
            s.keys = t < 0.55 ? "↓" : root.keys; s.down = (t > 0.2 && t < 0.3) || (t > 0.4 && t < 0.5) || (t > 0.62 && t < 0.72)
            break
        }
        case "search": {
            s.query = typed("meet", t, 0.1, 0.5)
            const q = s.query
            s.cards = [c("Meeting moved to Thursday", { hi: true }),
                       c("Grocery list: eggs, milk", { op: q.length >= 2 ? 0.15 : 1 }),
                       c("Weekly meet notes", { op: 1 })]
            break
        }
        case "paste_clean": {
            const clean = t > 0.5
            s.cards = [c(clean ? "shop.com/item?id=42" : "shop.com/item?id=42&utm_source=mail&fbclid=Xy9", { hi: true, flash: flashAt(0.5) }),
                       c("Thanks, see you soon!")]
            s.keys = root.keys; s.down = t > 0.38 && t < 0.52
            break
        }
        case "queue": {
            const b = n => t > 0.1 + n * 0.15 ? n + 1 : 0
            const gone = n => ph(t, 0.62 + n * 0.12, 0.7 + n * 0.12)
            s.cards = [c("Name: Ada", { badge: b(0), op: 1 - gone(0) }), c("Street 12", { badge: b(1), op: 1 - gone(1) }),
                       c("Istanbul", { badge: b(2), op: 1 - gone(2) })]
            s.keys = t < 0.55 ? root.keys : "Return"; s.down = (t > 0.1 && t < 0.18) || (t > 0.25 && t < 0.33) || (t > 0.4 && t < 0.48) || (t > 0.6 && t < 0.66)
            break
        }
        case "menu": {
            s.cards = [c("hello world", { hi: true }), c("#E58F6F")]
            s.cursor = { x: 0.55, y: 0.3, click: t > 0.25 && t < 0.32 }
            if (t > 0.3) s.menu = ["Paste cleaned", "Edit, then paste", "Convert", "Folder"]
            s.menuHi = t > 0.55 ? Math.min(3, Math.floor((t - 0.55) * 12)) : -1
            break
        }
        case "convert": {
            const txt = t < 0.55 ? "hello world" : "HELLO WORLD"
            s.cards = [c(txt, { hi: true, flash: flashAt(0.55) }), c('{"a":1,"b":2}', { mono: true })]
            if (t > 0.15 && t < 0.55) s.menu = ["UPPERCASE", "Title Case", "Base64 encode"]
            s.menuHi = t > 0.35 ? 0 : -1
            break
        }
        case "edit": {
            s.cards = [c("Hi Ada," + typed(" the files are ready!", t, 0.3, 0.75), { hi: true, flash: flashAt(0.85) })]
            s.keys = root.keys; s.down = t > 0.1 && t < 0.25
            break
        }
        case "folders": {
            s.cards = [c("My address: Street 12", { tape: t > 0.3, chip: t > 0.55 ? "Personal" : "", hi: true }),
                       c("Invoice template", { tape: true, chip: "Work" })]
            s.keys = root.keys; s.down = t > 0.2 && t < 0.32
            break
        }
        case "templates": {
            const filled = t > 0.5
            s.cards = [c(filled ? "Report – 12.11.2026" : "Report – {date}", { hi: true, tape: true, flash: flashAt(0.5) }),
                       c(filled ? "Signed: Ada · 14:30" : "Signed: Ada · {time}", { tape: true })]
            break
        }
        case "secrets": {
            s.cards = [c("ghp_8fK2aQ91LmZ", { dots: t > 0.25, hi: true, op: 1 - ph(t, 0.7, 0.85) }), c("Lunch at noon?")]
            break
        }
        case "quick_numbers": {
            s.cards = [c("Meeting moved to Thursday", { badge: 0, flash: flashAt(0.62) }), c("https://example.com"), c("Thanks!")]
            s.keys = t < 0.5 ? "Alt" : "Alt + 1"; s.down = t > 0.15 && t < 0.7
            s.numbers = t > 0.15 && t < 0.7
            break
        }
        case "app_filter": {
            s.query = typed("@firefox", t, 0.1, 0.5)
            const f = s.query.length > 3
            s.cards = [c("https://example.com", { chip: "Firefox", hi: true }), c("TODO: call Ada", { chip: "Telegram", op: f ? 0.15 : 1 }),
                       c("https://docs.qt.io", { chip: "Firefox" })]
            break
        }
        }
        return s
    }

    // ---- drawing ----

    Rectangle {
        anchors.fill: parent
        radius: 12
        color: Theme.paper
        border.width: 1; border.color: Theme.edge
    }

    // mini search field
    Rectangle {
        id: miniSearch
        x: 12; y: 10
        width: parent.width - 24; height: 20; radius: 7
        color: Theme.sheet
        border.width: 1; border.color: root.sc.query !== "" ? Theme.accent : Theme.edge
        Text {
            x: 10; anchors.verticalCenter: parent.verticalCenter
            text: root.sc.query !== "" ? root.sc.query + "│" : "Search…"
            color: root.sc.query !== "" ? Theme.ink : Theme.pencil
            font.family: Theme.sans; font.pixelSize: 10
        }
    }

    // mini cards
    Column {
        x: 12; y: 38
        width: parent.width - 24
        spacing: 5
        Repeater {
            model: root.sc.cards.length
            Rectangle {
                required property int index
                readonly property var cd: root.sc.cards[index]
                width: parent.width; height: 24; radius: 6
                color: Theme.sheet
                opacity: cd.op
                border.width: cd.hi ? 1.5 : 1
                border.color: cd.hi ? Theme.accent : Theme.edge
                Behavior on opacity { NumberAnimation { duration: 160 } }
                Rectangle { anchors.fill: parent; radius: 6; color: Theme.accent; opacity: cd.flash * 0.45 }
                Rectangle { visible: cd.tape; x: -4; y: 3; width: 18; height: 7; radius: 1.5; rotation: -38; color: Theme.alpha(Theme.sage, 0.9) }
                Text {
                    x: 12; anchors.verticalCenter: parent.verticalCenter
                    width: parent.width - 80
                    text: cd.dots ? "••••••••••" : cd.text
                    elide: Text.ElideRight
                    color: Theme.ink
                    font.family: cd.mono || cd.dots ? Theme.mono : Theme.sans
                    font.pixelSize: 10
                }
                Rectangle {
                    visible: cd.chip !== ""
                    anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                    width: chipT.implicitWidth + 10; height: 13; radius: 6.5
                    color: Theme.alpha(Theme.sage, 0.35)
                    Text { id: chipT; anchors.centerIn: parent; text: cd.chip; color: Theme.ink; font.family: Theme.sans; font.pixelSize: 8; font.weight: Font.DemiBold }
                }
                // paste queue number
                Rectangle {
                    x: -6; anchors.verticalCenter: parent.verticalCenter
                    width: 15; height: 15; radius: 7.5
                    color: Theme.accent; border.width: 1.5; border.color: Theme.sheet
                    scale: cd.badge > 0 ? 1 : 0
                    Behavior on scale { NumberAnimation { duration: 220; easing.type: Easing.OutBack; easing.overshoot: 2.4 } }
                    Text { anchors.centerIn: parent; text: cd.badge; color: Theme.sheet; font.family: Theme.sans; font.pixelSize: 8; font.weight: Font.Bold }
                }
                // Alt number
                Rectangle {
                    visible: root.sc.numbers === true
                    anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                    width: 14; height: 13; radius: 3; color: Theme.tape
                    Text { anchors.centerIn: parent; text: index + 1; color: Theme.ink; font.family: Theme.mono; font.pixelSize: 8; font.weight: Font.Bold }
                }
            }
        }
    }

    // mini popup menu
    Rectangle {
        visible: root.sc.menu.length > 0
        x: parent.width * 0.42; y: 50
        width: Math.min(150, parent.width * 0.5); height: menuCol.implicitHeight + 8; radius: 7
        color: Theme.sheet
        border.width: 1; border.color: Theme.edge
        Column {
            id: menuCol
            x: 4; y: 4; width: parent.width - 8
            Repeater {
                model: root.sc.menu
                Rectangle {
                    required property int index
                    required property string modelData
                    width: parent.width; height: 15; radius: 4
                    color: index === root.sc.menuHi ? Theme.alpha(Theme.tape, 0.9) : "transparent"
                    Text { x: 6; anchors.verticalCenter: parent.verticalCenter; text: modelData; color: Theme.ink; font.family: Theme.sans; font.pixelSize: 9 }
                }
            }
        }
    }

    // mouse pointer
    Item {
        visible: root.sc.cursor !== null
        x: root.sc.cursor ? root.sc.cursor.x * root.width : 0
        y: root.sc.cursor ? root.sc.cursor.y * root.height + 14 : 0
        Rectangle {
            anchors.centerIn: parent
            width: 22; height: 22; radius: 11
            color: Theme.alpha(Theme.accent, 0.35)
            scale: root.sc.cursor && root.sc.cursor.click ? 1 : 0
            Behavior on scale { NumberAnimation { duration: 120 } }
        }
        Text { text: "➤"; rotation: -120; color: Theme.ink; font.pixelSize: 14 }
    }

    // keycaps of the shortcut being "pressed"
    Row {
        visible: root.sc.keys !== ""
        anchors { right: parent.right; bottom: parent.bottom; margins: 8 }
        spacing: 3
        Repeater {
            model: root.sc.keys.split(" + ")
            Rectangle {
                required property string modelData
                width: Math.max(20, kt.implicitWidth + 10); height: 20; radius: 5
                color: root.sc.down ? Theme.tape : Theme.sheet
                border.width: 1; border.color: Qt.darker(Theme.edge, 1.15)
                y: root.sc.down ? 1.5 : 0
                Rectangle {
                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                    height: root.sc.down ? 1 : 2.5
                    radius: 5
                    color: Theme.edge
                    z: -1 }
                Text { id: kt; anchors.centerIn: parent; text: modelData; color: Theme.ink; font.family: Theme.mono; font.pixelSize: 9; font.weight: Font.Bold }
            }
        }
    }
}
