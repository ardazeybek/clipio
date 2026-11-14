// Setup window: installs, updates or removes Clipio with a short paper-themed animation.
// The logo is built from pieces (two note sheets, tape, paper clip) that settle in on open;
// progress is a pencil line on a ruled line; the end draws a check mark and drops paper scraps.
import QtQuick
import QtQuick.Window
import "components"

Window {
    id: win
    required property var setup

    width: 460; height: 430
    visible: true
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.Window
    title: setup.mode === "uninstall" ? "Remove Clipio" : "Clipio Setup"

    // all durations and curves of this window in one place
    QtObject {
        id: motion
        readonly property int enter: 520        // logo pieces settling in
        readonly property int stagger: 90       // delay between pieces
        readonly property int swap: 220         // text crossfades
        readonly property int pencil: 420       // progress line catching up
        readonly property int check: 520        // check mark drawing
        readonly property real overshoot: 1.6
    }

    readonly property bool working: setup.state === "working"
    readonly property bool done: setup.state === "done"
    readonly property bool failed: setup.state === "failed"
    readonly property bool removing: setup.mode === "uninstall"
    readonly property bool same: setup.mode === "update" && setup.oldVersion === setup.version

    // ---- texts for each moment ----
    function headline() {
        if (done) return removing ? "Clipio was removed" : (setup.mode === "update" ? "Clipio is up to date!" : "Clipio is ready!")
        if (failed) return "Something went wrong"
        if (working) return setup.step + "…"
        if (removing) return "Remove Clipio?"
        if (same) return "Reinstall Clipio"
        return setup.mode === "update" ? "Update Clipio" : "Install Clipio"
    }
    function subline() {
        if (done && removing) return "Your saved history and settings were kept."
        if (done) return hint()
        if (failed) return setup.error
        if (working) return removing ? "Just a moment." : "This takes a few seconds."
        if (removing) return "The app goes away. Your history stays on this computer."
        if (same) return "Version " + setup.version + " is already installed. Reinstalling keeps your history."
        if (setup.mode === "update") return "Version " + setup.oldVersion + "  →  " + setup.version + ". Your history stays."
        return "A cozy clipboard history. Everything you copy, kept on paper."
    }
    // How to open Clipio on this computer
    function hint() {
        const wayland = Qt.platform.pluginName.indexOf("wayland") >= 0
        if (Qt.platform.os === "linux" && wayland)
            return "Bind the command  clipio toggle  to a key in your desktop's shortcut settings."
        const k = (setup.hotkey || "").split("+").map(p => p === "cmd" ? "⌘" : p === "shift" ? "⇧" : p.charAt(0).toUpperCase() + p.slice(1))
        return "Press " + k.join(Qt.platform.os === "osx" ? "" : " + ") + " anytime to open your clipboard."
    }

    // ---- paper card with its own shadow ----
    Rectangle {
        id: shade
        anchors.fill: card; anchors.margins: -2
        anchors.topMargin: 6; anchors.bottomMargin: -10
        radius: Theme.radius + 2
        color: Theme.shadow
        opacity: card.opacity * 0.6
    }
    Rectangle {
        id: card
        anchors.fill: parent; anchors.margins: 16
        radius: Theme.radius
        color: Theme.paper
        border.color: Theme.edge; border.width: 1
        opacity: 0; scale: 0.96
        Component.onCompleted: { opacity = 1; scale = 1; intro.start() }
        Behavior on opacity { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
        Behavior on scale { NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }

        // drag the window by its paper
        DragHandler { target: null; onActiveChanged: if (active) win.startSystemMove() }

        // close button (top right)
        Rectangle {
            id: closeBtn
            anchors { right: parent.right; top: parent.top; margins: 12 }
            width: 30; height: 30; radius: 15
            color: closeMouse.containsMouse ? Theme.alpha(Theme.danger, 0.12) : "transparent"
            visible: !win.working
            Behavior on color { ColorAnimation { duration: 140 } }
            Repeater {
                model: [45, -45]
                Rectangle { anchors.centerIn: parent; width: 14; height: 2.5; radius: 1.25; color: Theme.danger; rotation: modelData }
            }
            MouseArea { id: closeMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: Qt.quit() }
        }

        // ---- logo built from pieces ----
        Item {
            id: logo
            width: 150; height: 150
            anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 26 }
            scale: win.done ? 1.04 : 1
            Behavior on scale { NumberAnimation { duration: 400; easing.type: Easing.OutBack; easing.overshoot: 2 } }

            // back sheet (sage)
            Rectangle {
                id: back
                x: 22; y: 28; width: 86; height: 100; radius: 12
                color: Theme.sage
                rotation: -9; opacity: 0
                transform: Translate { id: backT; x: -40 }
            }
            // paper stack under the front sheet
            Rectangle {
                x: 44; y: 34; width: 86; height: 100; radius: 12
                color: Theme.stack; rotation: front.rotation; opacity: front.opacity
                transform: Translate { y: frontT.y }
            }
            // front sheet with ruled lines; on success its lines become a check mark
            Rectangle {
                id: front
                x: 38; y: 30; width: 86; height: 100; radius: 12
                color: Theme.sheet; border.color: Theme.edge; border.width: 2
                rotation: 5; opacity: 0
                transform: Translate { id: frontT; y: -50 }
                Repeater {
                    model: [{ y: 32, w: 56 }, { y: 50, w: 56 }, { y: 68, w: 34 }]
                    Rectangle {
                        x: 15; y: modelData.y; width: modelData.w; height: 6; radius: 3
                        color: Theme.edge
                        opacity: checkMark.t > 0 ? 1 - checkMark.t : 1
                    }
                }
                Canvas {
                    id: checkMark
                    anchors.fill: parent
                    property real t: 0
                    onTChanged: requestPaint()
                    onPaint: {
                        const c = getContext("2d")
                        c.reset()
                        if (t <= 0) return
                        c.strokeStyle = win.removing ? Theme.pencil : Theme.sage
                        c.lineWidth = 8; c.lineCap = "round"; c.lineJoin = "round"
                        // two strokes: short down-right, then long up-right
                        const p = [[24, 52], [38, 66], [64, 34]]
                        const l1 = Math.hypot(14, 14), l2 = Math.hypot(26, 32), d = t * (l1 + l2)
                        c.beginPath(); c.moveTo(p[0][0], p[0][1])
                        if (d <= l1) c.lineTo(p[0][0] + 14 * d / l1, p[0][1] + 14 * d / l1)
                        else { c.lineTo(p[1][0], p[1][1]); const f = (d - l1) / l2; c.lineTo(p[1][0] + 26 * f, p[1][1] - 32 * f) }
                        c.stroke()
                    }
                }
            }
            // mustard tape
            Rectangle {
                id: tape
                x: 30; y: 22; width: 40; height: 15; radius: 2
                color: Theme.tape; rotation: -18; opacity: 0; scale: 1.4
            }
            // peach paper clip (drawn once)
            Canvas {
                id: clip
                x: 86; y: -4; width: 44; height: 92
                opacity: 0
                transform: Translate { id: clipT; y: -30 }
                onPaint: {
                    const c = getContext("2d")
                    c.strokeStyle = Theme.accent; c.lineWidth = 8; c.lineCap = "round"; c.lineJoin = "round"
                    c.beginPath()
                    c.moveTo(30, 6); c.lineTo(30, 56); c.arc(18, 56, 12, 0, Math.PI, false)
                    c.lineTo(6, 18); c.arc(14, 18, 8, Math.PI, 0, false); c.lineTo(22, 50)
                    c.stroke()
                }
            }

            // pieces settle in one after another
            ParallelAnimation {
                id: intro
                SequentialAnimation {
                    ParallelAnimation {
                        NumberAnimation { target: back; property: "opacity"; to: 1; duration: motion.enter * 0.5 }
                        NumberAnimation { target: backT; property: "x"; to: 0; duration: motion.enter; easing.type: Easing.OutBack; easing.overshoot: motion.overshoot }
                    }
                }
                SequentialAnimation {
                    PauseAnimation { duration: motion.stagger }
                    ParallelAnimation {
                        NumberAnimation { target: front; property: "opacity"; to: 1; duration: motion.enter * 0.5 }
                        NumberAnimation { target: frontT; property: "y"; to: 0; duration: motion.enter; easing.type: Easing.OutBack; easing.overshoot: motion.overshoot }
                    }
                }
                SequentialAnimation {
                    PauseAnimation { duration: motion.stagger * 3 }
                    ParallelAnimation {
                        NumberAnimation { target: clip; property: "opacity"; to: 1; duration: 180 }
                        NumberAnimation { target: clipT; property: "y"; to: 0; duration: motion.enter; easing.type: Easing.OutBack; easing.overshoot: 2.2 }
                    }
                }
                SequentialAnimation {
                    PauseAnimation { duration: motion.stagger * 5 }
                    ParallelAnimation {
                        NumberAnimation { target: tape; property: "opacity"; to: 0.95; duration: 120 }
                        NumberAnimation { target: tape; property: "scale"; to: 1; duration: 260; easing.type: Easing.OutBack; easing.overshoot: 2.5 }
                    }
                }
            }
        }

        // ---- texts ----
        Column {
            id: texts
            anchors { top: logo.bottom; topMargin: 14; left: parent.left; right: parent.right; leftMargin: 34; rightMargin: 34 }
            spacing: 8
            SwapText {
                value: win.headline()
                color: win.failed ? Theme.danger : Theme.ink
                font.pixelSize: 22; font.weight: Font.Bold
            }
            SwapText {
                value: win.subline()
                color: Theme.pencil
                font.pixelSize: 14
            }
            SwapText {
                visible: win.done && setup.missing.length > 0
                value: "Please install with your package manager: " + setup.missing.join(", ")
                color: Theme.danger
                font.pixelSize: 13
            }
        }

        // ---- pencil progress on a ruled line ----
        Item {
            id: ruler
            anchors { left: parent.left; right: parent.right; bottom: buttons.top; leftMargin: 44; rightMargin: 44; bottomMargin: 22 }
            height: 14
            opacity: win.working ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: motion.swap } }
            Rectangle { anchors.verticalCenter: parent.verticalCenter; width: parent.width; height: 2; radius: 1; color: Theme.edge }
            Rectangle {
                id: ink
                anchors.verticalCenter: parent.verticalCenter
                height: 4; radius: 2; color: Theme.accent
                width: parent.width * setup.progress
                Behavior on width { NumberAnimation { duration: motion.pencil; easing.type: Easing.OutCubic } }
            }
            // the pencil tip riding on the line
            Rectangle {
                x: ink.width - 3; y: -9
                width: 6; height: 22; radius: 2
                color: Theme.tape; border.color: Qt.darker(Theme.tape, 1.2); border.width: 1
                rotation: 30
                Rectangle { anchors.bottom: parent.bottom; anchors.horizontalCenter: parent.horizontalCenter; width: 3; height: 5; radius: 1; color: Theme.ink }
            }
        }

        // ---- buttons ----
        Row {
            id: buttons
            anchors { bottom: parent.bottom; bottomMargin: 26; horizontalCenter: parent.horizontalCenter }
            spacing: 10
            opacity: win.working ? 0 : 1
            enabled: !win.working
            Behavior on opacity { NumberAnimation { duration: motion.swap } }

            PaperButton {
                visible: !win.done
                label: win.failed ? "Try again" : (win.removing ? "Remove" : (win.same ? "Reinstall" : setup.mode === "update" ? "Update" : "Install"))
                solid: true
                fill: win.removing ? Theme.danger : Theme.accent
                onClicked: setup.start()
            }
            PaperButton {
                visible: win.done && !win.removing
                label: "Open Clipio"
                solid: true
                onClicked: { setup.openClipio(); Qt.quit() }
            }
            PaperButton {
                label: win.done ? "Close" : "Cancel"
                onClicked: Qt.quit()
            }
        }

        // ---- success: draw the check, drop paper scraps ----
        Connections {
            target: setup
            function onChanged() {
                if (setup.state === "done" && checkMark.t === 0) celebrate.start()
            }
        }
        SequentialAnimation {
            id: celebrate
            NumberAnimation { target: checkMark; property: "t"; to: 1; duration: motion.check; easing.type: Easing.InOutCubic }
            ScriptAction { script: if (!win.removing) confetti.burst() }
        }
        Item {
            id: confetti
            anchors.fill: parent
            property bool live: false
            function burst() { live = true; scrapTimer.restart() }
            Timer { id: scrapTimer; interval: 1500; onTriggered: confetti.live = false }
            Repeater {
                model: confetti.live ? 16 : 0
                Rectangle {
                    id: bit
                    readonly property real dir: (index / 16) * Math.PI * 2 + Math.random() * 0.3
                    readonly property real dist: 70 + Math.random() * 70
                    width: 8 + (index % 3) * 3; height: 5 + (index % 2) * 4; radius: 1.5
                    color: [Theme.accent, Theme.tape, Theme.sage, Theme.sheet][index % 4]
                    border.color: Theme.edge; border.width: index % 4 === 3 ? 1 : 0
                    x: logo.x + logo.width / 2; y: logo.y + logo.height / 2
                    NumberAnimation on x { to: bit.x + Math.cos(bit.dir) * bit.dist; duration: 900; easing.type: Easing.OutCubic }
                    NumberAnimation on y { to: bit.y + Math.sin(bit.dir) * bit.dist * 0.7 + 60; duration: 1300; easing.type: Easing.OutQuad }
                    NumberAnimation on rotation { from: 0; to: (index % 2 ? 1 : -1) * 280; duration: 1300 }
                    NumberAnimation on opacity { from: 1; to: 0; duration: 1400; easing.type: Easing.InQuad }
                }
            }
        }
    }

    // text that crossfades and lifts a little when it changes
    component SwapText: Text {
        id: st
        width: parent ? parent.width : 0
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.Wrap
        font.family: Theme.sans
        property string value: ""          // wanted text; `text` follows it after the fade
        onValueChanged: if (text === "") text = value; else if (value !== text) swap.restart()
        SequentialAnimation {
            id: swap
            NumberAnimation { target: st; property: "opacity"; to: 0; duration: motion.swap * 0.45 }
            ScriptAction { script: st.text = st.value }
            ParallelAnimation {
                NumberAnimation { target: st; property: "opacity"; to: 1; duration: motion.swap; easing.type: Easing.OutCubic }
                NumberAnimation { target: lift; property: "y"; from: 6; to: 0; duration: motion.swap; easing.type: Easing.OutCubic }
            }
        }
        transform: Translate { id: lift }
    }
}
