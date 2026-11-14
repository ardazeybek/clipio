// Main panel: a paper page with search, tabs, folders, the card list, card menu, editor, paste queue and keyboard control.
import QtQuick
import QtQuick.Effects
import QtQuick.Window
import Clipio

Item {
    id: root

    property bool shown: false
    property int openSerial: 0          // grows on every open; cards replay their enter animation
    property string dialog: ""          // open dialog: "" | clear | settings | menu | edit
    property int menuCid: -1            // card the menu or editor works on
    property var menuConversions: []    // conversions offered for that card
    property bool altHeld: false        // Alt is down: cards show their Alt+number
    property string toast: ""           // short message at the bottom
    property real open: 0               // open progress (opacity / slide)
    property real pop: 0                // open "bounce" progress (scale)
    property bool hoverArmed: false     // to ignore the fake mouse event right after opening
    property real lastGx: -1
    property real lastGy: -1
    property int pendingCid: -1
    property bool pendingPaste: true
    signal closeRequested()

    width: 520
    height: 660
    opacity: open
    scale: 0.9 + 0.1 * pop
    transform: Translate { y: (1 - root.open) * (root.shown ? 30 : 14) }

    Behavior on open { NumberAnimation { duration: root.shown ? 300 : 150; easing.type: root.shown ? Easing.OutCubic : Easing.InCubic } }
    Behavior on pop { NumberAnimation { duration: root.shown ? 520 : 150; easing.type: root.shown ? Easing.OutBack : Easing.InCubic; easing.overshoot: 1.6 } }

    onShownChanged: {
        open = shown ? 1 : 0
        pop = shown ? 1 : 0
        if (shown) { opened(); tapeAnim.restart(); logoAnim.restart() }
    }

    // Reset the state when the panel opens and focus the search field
    function opened() {
        dialog = ""
        hoverArmed = false
        Store.tab = "all"
        input.text = ""
        Store.query = ""
        Store.marked = []
        altHeld = false
        resetSelection()
        openSerial++
        Store.reload()
        Qt.callLater(() => input.forceActiveFocus())
    }

    // Select the card under the mouse only when the mouse really moved
    function hoverAt(i, gx, gy) {
        const moved = gx !== lastGx || gy !== lastGy
        lastGx = gx; lastGy = gy
        if (hoverArmed && moved) list.currentIndex = i
        hoverArmed = true
    }

    // After a search or tab change select the first card and scroll to the top
    function resetSelection() {
        Qt.callLater(() => {
            scrollAnim.stop()
            list.currentIndex = Store.count > 0 ? 0 : -1
            list.contentY = list.originY - list.topMargin   // to the very top, including the top margin
        })
    }

    // Paste or copy an item: flash first, then close the panel, then run the action
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
            if (root.pendingCid >= 0) {
                if (root.pendingClean) Store.activateClean(root.pendingCid)
                else Store.activate(root.pendingCid, root.pendingPaste)
            }
            root.pendingCid = -1
            root.pendingClean = false
        }
    }

    // Move the selection: arrows wrap around at the ends, page keys stop there
    function move(delta) {
        const n = Store.count
        if (n === 0) return
        const i = Math.max(0, list.currentIndex)
        list.currentIndex = Math.abs(delta) === 1 ? (i + delta + n) % n : Math.max(0, Math.min(n - 1, i + delta))
        ensureVisible(list.currentIndex)
    }

    // Scroll smoothly until the given card is visible
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

    // Select the card with this cid (after pinning moved it)
    function selectCid(cid) {
        for (let k = 0; k < Store.count; k++)
            if (Store.model.get(k).cid === cid) { list.currentIndex = k; ensureVisible(k); return }
    }

    // Switch to the next or previous tab
    function cycleTab(dir) {
        const keys = ["all", "text", "image", "pinned"]
        Store.tab = keys[(keys.indexOf(Store.tab) + dir + keys.length) % keys.length]
        resetSelection()
    }

    // cid of the selected card (-1 when none)
    function currentCid() {
        return list.currentIndex >= 0 && list.currentIndex < Store.count ? Store.model.get(list.currentIndex).cid : -1
    }

    // Open the card menu for a card
    function openMenu(cid) {
        if (cid < 0) return
        menuCid = cid
        menuConversions = Store.find(cid) && Store.find(cid).kind === "text" ? Backend.conversions(cid) : []
        folderInput.text = ""
        dialog = "menu"
    }

    // Open the editor with a card's text
    function openEditor(cid) {
        const it = Store.find(cid)
        if (!it || it.kind !== "text") return
        menuCid = cid
        editor.text = it.preview.length < it.chars ? Backend.fullText(cid) : it.preview
        dialog = "edit"
        Qt.callLater(() => { editor.forceActiveFocus(); editor.cursorPosition = editor.length })
    }

    // Close a dialog and give the search field its focus back
    function closeDialog() { dialog = ""; input.forceActiveFocus() }

    // Show a short message at the bottom for a moment
    function showToast(msg) { toast = msg; toastTimer.restart() }
    Timer { id: toastTimer; interval: 2600; onTriggered: root.toast = "" }

    // Paste or copy a card through the closing animation (cid instead of index)
    function activateCid(cid, mode) {
        dialog = ""
        pendingCid = cid
        pendingPaste = mode !== "copy"
        pendingClean = mode === "clean"
        closeTimer.restart()
    }
    property bool pendingClean: false

    // Enter: paste the queue when cards are marked, otherwise the selected card
    function enterPressed(shift) {
        if (Store.marked.length > 0) { Store.startQueue(); root.closeRequested(); return }
        if (shift) { const c = currentCid(); if (c >= 0) activateCid(c, "clean"); return }
        if (Store.queue.length > 0 && list.currentIndex < 0) { Backend.pasteNext(); return }
        activate(list.currentIndex, true)
    }

    // Select the card with this cid once the list has it (after a conversion or OCR)
    function selectWhenReady(cid) {
        Store.tab = "all"
        Qt.callLater(() => selectCid(cid))
    }
    Connections {
        target: Backend
        function onCreated(cid) { root.selectWhenReady(cid) }
        function onNotice(key) { root.showToast(Strings.t(key)) }
    }

    // Pin or unpin the selected item
    function pinCurrent() {
        if (list.currentIndex < 0 || list.currentIndex >= Store.count) return
        const cid = Store.model.get(list.currentIndex).cid
        Store.togglePin(cid)
        Qt.callLater(() => selectCid(cid))
    }

    // Delete the selected item
    function deleteCurrent() {
        if (list.currentIndex < 0 || list.currentIndex >= Store.count) return
        const i = list.currentIndex
        Store.remove(Store.model.get(i).cid)
        Qt.callLater(() => { list.currentIndex = Math.min(i, Store.count - 1) })
    }

    // Route key presses: fixed navigation keys first, then the user's shortcuts
    function handleKey(e) {
        if (dialog !== "") { dialogKey(e); return }
        const alt = e.modifiers & Qt.AltModifier
        e.accepted = true
        if (e.key === Qt.Key_Alt) { altHeld = Store.on("quick_numbers"); e.accepted = false; return }
        if (alt && Store.on("quick_numbers") && e.key >= Qt.Key_1 && e.key <= Qt.Key_9) { activate(e.key - Qt.Key_1, true); return }
        switch (e.key) {
        case Qt.Key_Down: move(1); return
        case Qt.Key_Up: move(-1); return
        case Qt.Key_PageDown: move(5); return
        case Qt.Key_PageUp: move(-5); return
        case Qt.Key_Escape:
            if (input.text !== "") input.text = ""
            else if (Store.marked.length > 0) Store.marked = []
            else root.closeRequested()
            return
        }
        if (!runAction(Store.actionFor(e), e)) e.accepted = false
    }

    // Run a shortcut action; false when the key should go to the search field instead
    function runAction(action, e) {
        switch (action) {
        case "paste": enterPressed(false); return true
        case "paste_clean": enterPressed(true); return true
        case "copy": if (input.selectedText !== "") return false; activate(list.currentIndex, false); return true
        case "menu": openMenu(currentCid()); return true
        case "edit": openEditor(currentCid()); return true
        case "mark": { const c = currentCid(); if (c >= 0) Store.toggleMark(c); return true }
        case "pin": pinCurrent(); return true
        case "delete":
            // while typing, Delete removes the character after the cursor, not a card
            if (input.text !== "" && (input.cursorPosition < input.text.length || input.selectedText !== "")) return false
            deleteCurrent(); return true
        case "next_tab": cycleTab(1); return true
        case "prev_tab": cycleTab(-1); return true
        case "settings": dialog = "settings"; return true
        }
        return false
    }

    // Keys while a dialog is open: Esc closes it, Enter confirms clearing
    function dialogKey(e) {
        e.accepted = true
        if (e.key === Qt.Key_Escape) closeDialog()
        else if ((e.key === Qt.Key_Return || e.key === Qt.Key_Enter) && dialog === "clear") confirmClear()
        else e.accepted = false
    }

    // Clear the history and close the dialog
    function confirmClear() {
        Store.clearAll()
        dialog = ""
        input.forceActiveFocus()
    }

    // ---- view ----

    RectangularShadow {
        anchors.fill: bg
        radius: Theme.radius
        blur: 50
        offset: Qt.vector2d(0, 16)
        color: Theme.shadow
    }

    // paper page with a piece of tape on top
    Rectangle {
        id: bg
        anchors.fill: parent
        radius: Theme.radius
        color: Theme.paper
        border.width: 1
        border.color: Theme.edge

        // drag the window by any empty spot (the system moves it, so it works everywhere)
        MouseArea {
            anchors.fill: parent
            cursorShape: pressed ? Qt.ClosedHandCursor : Qt.ArrowCursor
            onPressed: if (root.Window.window) root.Window.window.startSystemMove()
            onReleased: input.forceActiveFocus()
        }
    }
    // top tape: drops in and sticks with a twist on open
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

    // search row: search field + pause + clear + settings
    Item {
        id: header
        anchors { top: parent.top; topMargin: 26; left: parent.left; right: parent.right; leftMargin: 16; rightMargin: 14 }
        height: 44

        // app logo: bounces in on open, wiggles on hover
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
                // the magnifier wiggles while typing
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
                Keys.onReleased: e => { if (e.key === Qt.Key_Alt) root.altHeld = false }

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
                enabled: Store.canClear          // nothing to clear: no question, button rests dim
                opacity: enabled ? 1 : 0.35
                Behavior on opacity { NumberAnimation { duration: 140 } }
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

    // tabs
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

    // folder chips inside the pinned tab
    Flickable {
        id: folders
        anchors { top: tabs.bottom; topMargin: 6; left: parent.left; right: parent.right; leftMargin: 16; rightMargin: 16 }
        height: visible ? 28 : 0
        visible: Store.tab === "pinned" && Store.tags.length > 0
        contentWidth: chipRow.implicitWidth
        clip: true
        flickableDirection: Flickable.HorizontalFlick
        Row {
            id: chipRow
            spacing: 6
            Repeater {
                model: [""].concat(Store.tags)
                PaperButton {
                    required property string modelData
                    height: 26
                    label: modelData === "" ? Strings.t("all") : modelData
                    checked: Store.folder === modelData
                    onClicked: { Store.folder = modelData; root.resetSelection(); input.forceActiveFocus() }
                }
            }
        }
    }

    // card list
    ListView {
        id: list
        objectName: "cardList"
        anchors { top: folders.bottom; topMargin: 8; left: parent.left; right: parent.right; bottom: queueBar.top; leftMargin: 9; rightMargin: 9; bottomMargin: 6 }
        clip: true
        spacing: 6
        topMargin: 10
        bottomMargin: 14
        model: Store.model
        currentIndex: 0
        boundsBehavior: Flickable.StopAtBounds
        maximumFlickVelocity: 3500
        cacheBuffer: 1600            // build cards ahead of time so scrolling never waits for them
        onMovementStarted: { scrollAnim.stop(); wheelAnim.stop() }

        // smooth mouse-wheel scrolling: each notch moves a target, the view glides to it
        property real wheelTarget: 0
        WheelHandler {
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            onWheel: event => list.wheelBy(event)
        }
        NumberAnimation { id: wheelAnim; target: list; property: "contentY"; duration: 260; easing.type: Easing.OutCubic }

        // Move the wheel target by one wheel event and glide there (touchpads follow directly)
        function wheelBy(event) {
            const minY = originY - topMargin
            const maxY = Math.max(minY, originY + contentHeight + bottomMargin - height)
            scrollAnim.stop()
            // touchpad: pixel deltas, follow the fingers 1:1
            if (event.pixelDelta.y !== 0) {
                wheelAnim.stop()
                contentY = Math.max(minY, Math.min(maxY, contentY - event.pixelDelta.y))
                return
            }
            // mouse wheel: 120 units per notch, about 110 px per notch
            const base = wheelAnim.running ? wheelTarget : contentY
            wheelTarget = Math.max(minY, Math.min(maxY, base - event.angleDelta.y / 120 * 110))
            wheelAnim.stop()
            wheelAnim.to = wheelTarget
            wheelAnim.start()
        }
        onCountChanged: if (currentIndex < 0 && count > 0) currentIndex = 0
        // if the selected card was deleted, go back to the first card
        onCurrentIndexChanged: if (currentIndex < 0) Qt.callLater(() => { if (list.currentIndex < 0 && list.count > 0) list.currentIndex = 0 })

        delegate: ClipCard {
            id: cardItem
            onHoverMoved: (gx, gy) => root.hoverAt(index, gx, gy)
            onPick: paste => root.activate(index, paste)
            onPinClicked: { list.currentIndex = index; root.pinCurrent() }
            onDeleteClicked: { list.currentIndex = index; root.deleteCurrent() }
            onMenuRequested: { list.currentIndex = index; root.openMenu(cid) }
            onMarkClicked: { list.currentIndex = index; Store.toggleMark(cid) }
            showNumber: root.altHeld
            Component.onCompleted: replay(root.open < 0.6 ? Math.min(index, 9) * 32 : 0)
            Connections {
                target: root
                function onOpenSerialChanged() { cardItem.replay(Math.min(cardItem.index, 9) * 32) }
            }
        }

        // cards play their own enter animation (an interrupted transition must not leave a card invisible)
        // removal only fades and shrinks a little, so nothing is cut at the list edge
        remove: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; to: 0; duration: 180 }
                NumberAnimation { property: "scale"; to: 0.96; duration: 180 }
            }
        }
        displaced: Transition { NumberAnimation { properties: "x,y"; duration: 280; easing.type: Easing.OutCubic } }
        move: Transition { NumberAnimation { properties: "x,y"; duration: 320; easing.type: Easing.OutCubic } }
    }

    // soft fade at the top edge of the list while scrolling
    Rectangle {
        anchors { left: list.left; right: list.right; top: list.top }
        height: 12
        visible: list.contentY > list.originY - list.topMargin + 1
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.paper }
            GradientStop { position: 1; color: Theme.alpha(Theme.paper, 0) }
        }
    }

    // soft fade into the paper at the bottom edge of the list
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

    // paste queue bar: marked cards, or items the backend still has to paste
    Rectangle {
        id: queueBar
        readonly property bool active: Store.marked.length > 0 || Store.queue.length > 0
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 12 }
        height: active ? 40 : 0
        visible: height > 1
        clip: true
        radius: 12
        color: Theme.alpha(Theme.accent, 0.16)
        border.width: 1; border.color: Theme.alpha(Theme.accent, 0.5)
        Behavior on height { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
        Text {
            anchors { left: parent.left; leftMargin: 14; right: clearQ.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
            text: Store.marked.length > 0 ? Strings.t("queued", Store.marked.length) : Strings.t("queueLeft", Store.queue.length)
            elide: Text.ElideRight
            color: Theme.ink
            font.family: Theme.sans
            font.pixelSize: 12; font.weight: Font.Medium
        }
        PaperButton {
            id: clearQ
            anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
            height: 28
            label: Strings.t("clearQueue")
            onClicked: { Store.clearQueue(); input.forceActiveFocus() }
        }
    }

    // short message (e.g. OCR found nothing)
    Rectangle {
        anchors { horizontalCenter: parent.horizontalCenter; bottom: queueBar.top; bottomMargin: 14 }
        z: 20
        width: toastText.implicitWidth + 28; height: 34; radius: 17
        color: Theme.ink
        opacity: root.toast !== "" ? 0.92 : 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 180 } }
        Text { id: toastText; anchors.centerIn: parent; text: root.toast; color: Theme.sheet; font.family: Theme.sans; font.pixelSize: 13 }
    }

    // card menu: clean paste, copy, edit, queue, convert, folder, OCR, ignore app
    Dialog {
        id: menuDialog
        anchors.fill: parent
        z: 10
        shown: root.dialog === "menu"
        title: Strings.t("menu")
        onDismissed: root.closeDialog()
        readonly property var it: root.menuCid >= 0 ? Store.find(root.menuCid) : null
        readonly property bool isText: it !== null && it.kind === "text"

        Flow {
            width: parent.width
            spacing: 6
            PaperButton { visible: menuDialog.isText; label: Strings.t("pasteClean"); solid: true; onClicked: root.activateCid(root.menuCid, "clean") }
            PaperButton { label: Strings.t("copyOnly"); onClicked: root.activateCid(root.menuCid, "copy") }
            PaperButton { visible: menuDialog.isText; label: Strings.t("edit"); onClicked: root.openEditor(root.menuCid) }
            PaperButton {
                label: Store.markNo(root.menuCid) > 0 ? Strings.t("queueRemove") : Strings.t("queueAdd")
                onClicked: { Store.toggleMark(root.menuCid); root.closeDialog() }
            }
            PaperButton {
                visible: menuDialog.it !== null && menuDialog.it.kind === "image"
                label: Store.ocr ? Strings.t("ocr") : Strings.t("ocrMissing")
                enabled: Store.ocr
                opacity: Store.ocr ? 1 : 0.55
                onClicked: { Backend.ocr(root.menuCid); root.showToast(Strings.t("reading")); root.closeDialog() }
            }
        }

        // conversions that work on this text
        Text {
            visible: root.menuConversions.length > 0
            text: Strings.t("convert")
            color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 12; font.weight: Font.Bold
        }
        Flow {
            visible: root.menuConversions.length > 0
            width: parent.width
            spacing: 6
            Repeater {
                model: root.menuConversions
                PaperButton {
                    required property string modelData
                    height: 30
                    label: Strings.t(modelData)
                    onClicked: { Backend.convert(root.menuCid, modelData); root.closeDialog() }
                }
            }
        }

        // folder: existing ones or a new name (a folder also pins the item)
        Text {
            text: Strings.t("folder")
            color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 12; font.weight: Font.Bold
        }
        Flow {
            width: parent.width
            spacing: 6
            Repeater {
                model: [""].concat(Store.tags)
                PaperButton {
                    required property string modelData
                    height: 30
                    label: modelData === "" ? Strings.t("noFolder") : modelData
                    checked: menuDialog.it !== null && menuDialog.it.tag === modelData
                    onClicked: { Store.setTag(root.menuCid, modelData); root.closeDialog() }
                }
            }
            Rectangle {
                width: 130; height: 30; radius: 10
                color: Theme.sheet
                border.width: 1; border.color: folderInput.activeFocus ? Theme.accent : Theme.edge
                TextInput {
                    id: folderInput
                    anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
                    verticalAlignment: TextInput.AlignVCenter
                    color: Theme.ink
                    font.family: Theme.sans; font.pixelSize: 13
                    clip: true
                    maximumLength: 40
                    onAccepted: if (text.trim() !== "") { Store.setTag(root.menuCid, text.trim()); root.closeDialog() }
                    Keys.onEscapePressed: root.closeDialog()
                    Text { visible: folderInput.text === ""; anchors.verticalCenter: parent.verticalCenter; text: Strings.t("folderHint"); color: Theme.pencil; font: folderInput.font }
                }
            }
        }

        PaperButton {
            visible: menuDialog.it !== null && menuDialog.it.source !== "" && menuDialog.it.source !== "Clipio" && menuDialog.it.source !== "OCR"
            label: Strings.t("ignoreApp", menuDialog.it ? Store.appName(menuDialog.it.source) : "")
            fill: Theme.danger; solid: true
            onClicked: { Store.setAppIgnored(menuDialog.it.source, true); root.closeDialog() }
        }
    }

    // editor: change the text, then paste or copy it (saved as a new item)
    Dialog {
        anchors.fill: parent
        z: 10
        shown: root.dialog === "edit"
        title: Strings.t("editTitle")
        onDismissed: root.closeDialog()
        Rectangle {
            width: parent.width
            height: 220
            radius: 10
            color: Theme.paper
            border.width: 1; border.color: editor.activeFocus ? Theme.accent : Theme.edge
            Flickable {
                id: editFlick
                anchors { fill: parent; margins: 10 }
                contentHeight: editor.implicitHeight
                clip: true
                TextEdit {
                    id: editor
                    width: editFlick.width
                    wrapMode: TextEdit.Wrap
                    textFormat: TextEdit.PlainText
                    color: Theme.ink
                    selectionColor: Theme.alpha(Theme.accent, 0.4)
                    selectedTextColor: Theme.ink
                    font.family: Theme.sans; font.pixelSize: 14
                    // keep the cursor in view while typing
                    onCursorRectangleChanged: {
                        if (cursorRectangle.y < editFlick.contentY) editFlick.contentY = cursorRectangle.y
                        else if (cursorRectangle.y + cursorRectangle.height > editFlick.contentY + editFlick.height)
                            editFlick.contentY = cursorRectangle.y + cursorRectangle.height - editFlick.height
                    }
                    Keys.onPressed: e => {
                        if (e.key === Qt.Key_Escape) { root.closeDialog(); e.accepted = true }
                        else if ((e.key === Qt.Key_Return || e.key === Qt.Key_Enter) && (e.modifiers & Qt.ControlModifier)) {
                            Backend.pasteEdited(editor.text, true); root.dialog = ""; e.accepted = true
                        }
                    }
                }
            }
        }
        Row {
            anchors.right: parent.right
            spacing: 8
            PaperButton { label: Strings.t("cancel"); onClicked: root.closeDialog() }
            PaperButton { label: Strings.t("copyIt"); onClicked: { Backend.pasteEdited(editor.text, false); root.dialog = "" } }
            PaperButton { label: Strings.t("pasteIt"); solid: true; onClicked: { Backend.pasteEdited(editor.text, true); root.dialog = "" } }
        }
    }

    // clear confirmation
    Dialog {
        anchors.fill: parent
        z: 10
        shown: root.dialog === "clear"
        title: Strings.t("clearTitle")
        onDismissed: root.closeDialog()
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

    // settings page: guide, shortcuts, features, storage
    Settings {
        anchors.fill: parent
        z: 10
        shown: root.dialog === "settings"
        onClosed: root.closeDialog()
    }
}
