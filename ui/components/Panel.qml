// Ana panel: kağıt sayfa; arama, sekmeler, kart listesi ve klavye kontrolü.
import QtQuick
import QtQuick.Effects

Item {
    id: root

    property bool shown: false
    property int openSerial: 0          // her açılışta artar; kartlar giriş animasyonunu yeniden oynatır
    property string dialog: ""          // açık iç pencere: "" | clear | settings
    property real dragX: 0              // sürükleme ile ortadan kayma
    property real dragY: 0
    property real open: 0               // açılış ilerlemesi (opaklık / kayma)
    property real pop: 0                // açılış "zıplama" ilerlemesi (ölçek)
    property bool hoverArmed: false     // açılıştaki sahte fare olayını yok saymak için
    property real lastGx: -1
    property real lastGy: -1
    property int pendingCid: -1
    property bool pendingPaste: true
    signal closeRequested()

    width: Math.min(520, parent.width - 40)
    height: Math.min(660, parent.height - 140)
    opacity: open
    scale: 0.9 + 0.1 * pop
    transform: Translate { y: (1 - root.open) * (root.shown ? 30 : 14) }

    Behavior on open { NumberAnimation { duration: root.shown ? 300 : 150; easing.type: root.shown ? Easing.OutCubic : Easing.InCubic } }
    Behavior on pop { NumberAnimation { duration: root.shown ? 520 : 150; easing.type: root.shown ? Easing.OutBack : Easing.InCubic; easing.overshoot: 1.6 } }

    onShownChanged: {
        if (shown) { dragX = 0; dragY = 0 }   // her açılışta ekranın ortasından başla
        open = shown ? 1 : 0
        pop = shown ? 1 : 0
        if (shown) { opened(); tapeAnim.restart(); logoAnim.restart() }
    }

    // Panel açılırken durumu sıfırla ve aramaya odaklan
    function opened() {
        dialog = ""
        hoverArmed = false
        Store.watching = true
        Store.tab = "all"
        input.text = ""
        Store.query = ""
        resetSelection()
        openSerial++
        Store.reload()
        Qt.callLater(() => input.forceActiveFocus())
    }

    // Fare gerçekten hareket ettiyse o kartı seç (kart altına gelen sahte olayları yok say)
    function hoverAt(i, gx, gy) {
        const moved = gx !== lastGx || gy !== lastGy
        lastGx = gx; lastGy = gy
        if (hoverArmed && moved) list.currentIndex = i
        hoverArmed = true
    }

    // Arama/sekme değişince seçimi ilk karta al ve başa kaydır
    function resetSelection() {
        Qt.callLater(() => {
            scrollAnim.stop()
            list.currentIndex = Store.count > 0 ? 0 : -1
            list.contentY = list.originY - list.topMargin   // üst boşluk dahil en başa
        })
    }

    // Seçili öğeyi yapıştır/kopyala: önce parlama, sonra paneli kapat, sonra komutu çalıştır
    function activate(i, paste) {
        if (i < 0 || i >= Store.count) return
        const item = list.itemAtIndex(i)
        if (item) item.flash()
        pendingCid = Store.model.get(i).cid
        pendingPaste = paste
        closeTimer.restart()
    }

    Timer {
        id: closeTimer
        interval: 150
        onTriggered: {
            root.closeRequested()
            if (root.pendingCid >= 0) Store.activate(root.pendingCid, root.pendingPaste)
            root.pendingCid = -1
        }
    }

    // Seçimi bir kart kadar kaydır (uçlarda başa/sona sar)
    function move(delta) {
        const n = Store.count
        if (n === 0) return
        list.currentIndex = (list.currentIndex + delta + n) % n
        ensureVisible(list.currentIndex)
    }

    // Verilen kartı yumuşak kaydırmayla görünür alana getir
    function ensureVisible(i) {
        const it = list.itemAtIndex(i)
        if (!it) { list.positionViewAtIndex(i, ListView.Contain); return }
        const minY = list.originY - list.topMargin
        const maxY = Math.max(minY, list.originY + list.contentHeight - list.height + list.bottomMargin)
        let target = list.contentY
        if (it.y - 6 < list.contentY) target = it.y - 6
        else if (it.y + it.height + 6 > list.contentY + list.height) target = it.y + it.height + 6 - list.height
        else return
        scrollAnim.stop()
        scrollAnim.to = Math.max(minY, Math.min(maxY, target))
        scrollAnim.restart()
    }
    NumberAnimation { id: scrollAnim; target: list; property: "contentY"; duration: 240; easing.type: Easing.OutCubic }

    // cid'e sahip kartı seç (sabitleme sonrası yer değişince)
    function selectCid(cid) {
        for (let k = 0; k < Store.count; k++)
            if (Store.model.get(k).cid === cid) { list.currentIndex = k; ensureVisible(k); return }
    }

    // Sekmeyi ileri/geri değiştir
    function cycleTab(dir) {
        const keys = ["all", "text", "image", "pinned"]
        Store.tab = keys[(keys.indexOf(Store.tab) + dir + keys.length) % keys.length]
        resetSelection()
    }

    // Seçili öğeyi sabitle/kaldır
    function pinCurrent() {
        if (list.currentIndex < 0 || list.currentIndex >= Store.count) return
        const cid = Store.model.get(list.currentIndex).cid
        Store.togglePin(cid)
        Qt.callLater(() => selectCid(cid))
    }

    // Seçili öğeyi sil
    function deleteCurrent() {
        if (list.currentIndex < 0 || list.currentIndex >= Store.count) return
        const i = list.currentIndex
        Store.remove(Store.model.get(i).cid)
        Qt.callLater(() => { list.currentIndex = Math.min(i, Store.count - 1) })
    }

    // Tuş basışlarını yönlendir
    function handleKey(e) {
        if (dialog !== "") { dialogKey(e); return }
        const ctrl = e.modifiers & Qt.ControlModifier
        const alt = e.modifiers & Qt.AltModifier
        const shift = e.modifiers & Qt.ShiftModifier
        e.accepted = true
        if (alt && e.key >= Qt.Key_1 && e.key <= Qt.Key_9) { activate(e.key - Qt.Key_1, true); return }
        switch (e.key) {
        case Qt.Key_Down: move(1); break
        case Qt.Key_Up: move(-1); break
        case Qt.Key_PageDown: move(5); break
        case Qt.Key_PageUp: move(-5); break
        case Qt.Key_Return: case Qt.Key_Enter: activate(list.currentIndex, !shift); break
        case Qt.Key_Delete: deleteCurrent(); break
        case Qt.Key_Tab: cycleTab(1); break
        case Qt.Key_Backtab: cycleTab(-1); break
        case Qt.Key_P: if (ctrl) pinCurrent(); else e.accepted = false; break
        case Qt.Key_Escape:
            if (input.text !== "") input.text = ""; else root.closeRequested()
            break
        default: e.accepted = false
        }
    }


    // İç pencere açıkken tuşlar: Esc kapatır, Enter temizlemeyi onaylar
    function dialogKey(e) {
        e.accepted = true
        if (e.key === Qt.Key_Escape) dialog = ""
        else if ((e.key === Qt.Key_Return || e.key === Qt.Key_Enter) && dialog === "clear") confirmClear()
    }

    // Temizlemeyi uygula ve pencereyi kapat
    function confirmClear() {
        Store.clearAll()
        dialog = ""
        input.forceActiveFocus()
    }

    // Paneli ekranda kalacak şekilde sınırlı kaydır
    function dragTo(nx, ny) {
        const mx = Math.max(0, (parent.width - width) / 2)
        const my = Math.max(0, (parent.height - height) / 2)
        dragX = Math.max(-mx, Math.min(mx, nx))
        dragY = Math.max(-my + 34, Math.min(my + 24, ny))
    }

    // ---- görünüm ----

    RectangularShadow {
        anchors.fill: bg
        radius: Theme.radius
        blur: 50
        offset: Qt.vector2d(0, 16)
        color: Theme.shadow
    }

    // kağıt sayfa ve üstte yapıştırılmış bant
    Rectangle {
        id: bg
        anchors.fill: parent
        radius: Theme.radius
        color: Theme.paper
        border.width: 1
        border.color: Theme.edge

        // boş yerden tutup sürükle; tıklama panelin arkasına (kapatmaya) geçmez
        MouseArea {
            anchors.fill: parent
            cursorShape: pressed ? Qt.ClosedHandCursor : Qt.ArrowCursor
            property point start
            property real sx
            property real sy
            onPressed: m => { start = mapToGlobal(m.x, m.y); sx = root.dragX; sy = root.dragY }
            onPositionChanged: m => {
                const g = mapToGlobal(m.x, m.y)
                root.dragTo(sx + g.x - start.x, sy + g.y - start.y)
            }
            onReleased: input.forceActiveFocus()
        }
    }
    // üst bant: açılışta yukarıdan düşüp dönerek yapışır
    Rectangle {
        id: tape
        anchors.horizontalCenter: parent.horizontalCenter
        y: -10
        width: 92; height: 22; radius: 3
        rotation: -2
        color: Theme.alpha(Theme.tape, 0.85)
    }
    SequentialAnimation {
        id: tapeAnim
        PropertyAction { target: tape; property: "opacity"; value: 0 }
        PauseAnimation { duration: 140 }
        ParallelAnimation {
            NumberAnimation { target: tape; property: "opacity"; to: 1; duration: 160 }
            NumberAnimation { target: tape; property: "scale"; from: 1.5; to: 1; duration: 420; easing.type: Easing.OutBack; easing.overshoot: 1.6 }
            NumberAnimation { target: tape; property: "rotation"; from: -14; to: -2; duration: 520; easing.type: Easing.OutBack; easing.overshoot: 2 }
        }
    }

    // arama satırı: arama alanı + duraklat + temizle
    Item {
        id: header
        anchors { top: parent.top; topMargin: 26; left: parent.left; right: parent.right; leftMargin: 16; rightMargin: 14 }
        height: 44

        // uygulama logosu: açılışta dönerek zıplar, üzerine gelince sallanır
        Image {
            id: logo
            anchors { left: parent.left; verticalCenter: parent.verticalCenter }
            width: 40; height: 40
            source: Qt.resolvedUrl("../assets/clipio.svg")
            sourceSize: Qt.size(120, 120)
            smooth: true
            opacity: Store.paused ? 0.5 : 1
            Behavior on opacity { NumberAnimation { duration: 260 } }
            rotation: logoMouse.containsMouse ? -8 : 0
            Behavior on rotation { NumberAnimation { duration: 380; easing.type: Easing.OutBack; easing.overshoot: 2.5 } }
            MouseArea { id: logoMouse; anchors.fill: parent; hoverEnabled: true }
        }
        SequentialAnimation {
            id: logoAnim
            PropertyAction { target: logo; property: "scale"; value: 0.3 }
            PauseAnimation { duration: 90 }
            NumberAnimation { target: logo; property: "scale"; to: 1; duration: 520; easing.type: Easing.OutBack; easing.overshoot: 2.2 }
        }

        Rectangle {
            id: field
            anchors { left: logo.right; leftMargin: 10; right: tools.left; rightMargin: 8; top: parent.top; bottom: parent.bottom }
            radius: 14
            color: Theme.sheet
            border.color: input.activeFocus ? Theme.accent : Theme.edge
            border.width: input.activeFocus ? 1.5 : 1
            Behavior on border.color { ColorAnimation { duration: 180 } }

            Icon {
                id: searchIcon
                x: 14; anchors.verticalCenter: parent.verticalCenter
                name: "search"; size: 16
                color: input.activeFocus ? Theme.accent : Theme.pencil
                // yazdıkça büyüteç kıpırdar
                SequentialAnimation {
                    id: wiggle
                    NumberAnimation { target: searchIcon; property: "rotation"; to: -14; duration: 70 }
                    NumberAnimation { target: searchIcon; property: "rotation"; to: 0; duration: 260; easing.type: Easing.OutBack; easing.overshoot: 3 }
                }
            }
            TextInput {
                id: input
                anchors { left: searchIcon.right; leftMargin: 10; right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                color: Theme.ink
                selectionColor: Theme.alpha(Theme.accent, 0.4)
                selectedTextColor: Theme.ink
                font.family: Theme.sans
                font.pixelSize: 15
                clip: true
                focus: true
                onTextChanged: {
                    Store.query = text
                    root.resetSelection()
                    wiggle.restart()
                }
                Keys.onPressed: e => root.handleKey(e)

                Text {
                    visible: input.text === ""
                    anchors.verticalCenter: parent.verticalCenter
                    text: Store.paused ? Strings.t("paused") : Strings.t("search")
                    color: Store.paused ? Theme.danger : Theme.pencil
                    font: input.font
                }
            }
        }

        Row {
            id: tools
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            IconButton {
                icon: Store.paused ? "play" : "pause"
                tint: Store.paused ? Theme.danger : Theme.pencil
                size: 34
                onClicked: { Store.togglePause(); input.forceActiveFocus() }
            }
            IconButton {
                icon: "trash"
                size: 34
                hoverTint: Theme.danger
                glow: Theme.danger
                onClicked: root.dialog = "clear"
            }
            IconButton {
                icon: "settings"
                size: 34
                hoverSpin: 90
                onClicked: root.dialog = "settings"
            }
        }
    }

    // sekmeler
    Tabs {
        id: tabs
        anchors { top: header.bottom; topMargin: 10; left: parent.left; leftMargin: 12 }
        current: Store.tab
        tabs: [
            { key: "all", label: Strings.t("all") },
            { key: "text", label: Strings.t("text") },
            { key: "image", label: Strings.t("image") },
            { key: "pinned", label: Strings.t("pinned") }
        ]
        onPicked: key => { Store.tab = key; root.resetSelection(); input.forceActiveFocus() }
    }

    // kart listesi
    ListView {
        id: list
        anchors { top: tabs.bottom; topMargin: 8; left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 9; rightMargin: 9; bottomMargin: 6 }
        clip: true
        spacing: 6
        topMargin: 10
        bottomMargin: 14
        model: Store.model
        currentIndex: 0
        boundsBehavior: Flickable.StopAtBounds
        maximumFlickVelocity: 3500
        onMovementStarted: scrollAnim.stop()
        onCountChanged: if (currentIndex < 0 && count > 0) currentIndex = 0
        // seçili kart silinip seçim boşa düşerse ilk karta dön
        onCurrentIndexChanged: if (currentIndex < 0) Qt.callLater(() => { if (list.currentIndex < 0 && list.count > 0) list.currentIndex = 0 })

        delegate: ClipCard {
            id: cardItem
            onHoverMoved: (gx, gy) => root.hoverAt(index, gx, gy)
            onPick: paste => root.activate(index, paste)
            onPinClicked: { list.currentIndex = index; root.pinCurrent() }
            onDeleteClicked: { list.currentIndex = index; root.deleteCurrent() }
            Component.onCompleted: replay(root.open < 0.6 ? Math.min(index, 9) * 32 : 0)
            Connections {
                target: root
                function onOpenSerialChanged() { cardItem.replay(Math.min(cardItem.index, 9) * 32) }
            }
        }

        // giriş animasyonunu kart kendisi oynatır (yarıda kesilen geçiş kartı görünmez bırakmasın)
        // çıkış yalnızca solar ve hafifçe küçülür: yana taşıp liste kenarında kesilmez
        remove: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; to: 0; duration: 180 }
                NumberAnimation { property: "scale"; to: 0.96; duration: 180 }
            }
        }
        displaced: Transition { NumberAnimation { properties: "x,y"; duration: 280; easing.type: Easing.OutCubic } }
        move: Transition { NumberAnimation { properties: "x,y"; duration: 320; easing.type: Easing.OutCubic } }
    }

    // listenin üst kenarında kaydırırken kartları yumuşakça gizleyen geçiş
    Rectangle {
        anchors { left: list.left; right: list.right; top: list.top }
        height: 12
        visible: list.contentY > list.originY - list.topMargin + 1
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.paper }
            GradientStop { position: 1; color: Theme.alpha(Theme.paper, 0) }
        }
    }

    // listenin alt kenarında kağıda karışan yumuşak geçiş
    Rectangle {
        anchors { left: list.left; right: list.right; bottom: list.bottom }
        height: 26
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.alpha(Theme.paper, 0) }
            GradientStop { position: 1; color: Theme.paper }
        }
    }

    EmptyState {
        anchors.fill: list
        opacity: Store.count === 0 ? 1 : 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 240 } }
        title: Store.total === 0 && Store.query === "" ? Strings.t("empty") : Strings.t("noMatch")
        sub: Store.total === 0 && Store.query === "" ? Strings.t("emptySub") : ""
    }

    // temizleme onayı
    Dialog {
        anchors.fill: parent
        z: 10
        shown: root.dialog === "clear"
        title: Strings.t("clearTitle")
        onDismissed: { root.dialog = ""; input.forceActiveFocus() }
        Text {
            width: parent.width
            text: Strings.t("clearSub")
            color: Theme.pencil
            font.family: Theme.sans
            font.pixelSize: 14
            wrapMode: Text.Wrap
            lineHeight: 1.2
        }
        Row {
            anchors.right: parent.right
            spacing: 8
            PaperButton { label: Strings.t("cancel"); onClicked: { root.dialog = ""; input.forceActiveFocus() } }
            PaperButton { label: Strings.t("clearYes"); solid: true; fill: Theme.danger; onClicked: root.confirmClear() }
        }
    }

    // ayarlar: saklama süresi
    Dialog {
        anchors.fill: parent
        z: 10
        shown: root.dialog === "settings"
        title: Strings.t("settings")
        onDismissed: { root.dialog = ""; input.forceActiveFocus() }
        Text {
            width: parent.width
            text: Strings.t("keepFor")
            color: Theme.ink
            font.family: Theme.sans
            font.pixelSize: 14; font.weight: Font.Medium
        }
        Row {
            id: dayRow
            width: parent.width
            spacing: 6
            Repeater {
                model: [1, 3, 7, 14, 30]
                PaperButton {
                    required property int modelData
                    width: (dayRow.width - dayRow.spacing * 4) / 5
                    label: Strings.t("days", modelData)
                    checked: Store.retentionDays === modelData
                    onClicked: Store.setRetention(modelData)
                }
            }
        }
        Text {
            width: parent.width
            text: Strings.t("keepNote")
            color: Theme.pencil
            font.family: Theme.sans
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }
        PaperButton {
            anchors.right: parent.right
            label: Strings.t("done"); solid: true
            onClicked: { root.dialog = ""; input.forceActiveFocus() }
        }
    }
}
