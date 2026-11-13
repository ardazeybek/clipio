// One clipboard card: note-paper look, content by kind, source app and folder, queue number, pin/delete when selected.
import QtQuick
import QtQuick.Effects

Item {
    id: root

    required property int index
    required property int cid
    required property string kind
    required property string hint
    required property string meta
    required property string preview
    required property string image
    required property int imgW
    required property int imgH
    required property bool pinned
    required property real used
    required property string source
    required property string tag
    required property bool secret
    required property string title
    required property string rich
    required property bool template

    property bool showNumber: false                 // Alt is held: show the Alt+number shortcut
    readonly property int markNo: Store.markNo(cid) // place in the paste queue (0 = not queued)

    readonly property bool selected: ListView.isCurrentItem
    readonly property bool hot: selected || press.containsMouse
    property real appear: 1        // enter animation progress (0..1)
    // lift: the selected card rises from the stack, a hovered one moves a little
    property real pickScale: 1     // paste bounce
    property real lift: selected ? 1 : (press.containsMouse ? 0.45 : 0)
    Behavior on lift { NumberAnimation { duration: 260; easing.type: Easing.OutBack; easing.overshoot: 1.8 } }

    signal pick(bool paste)
    signal hoverMoved(real gx, real gy)
    signal pinClicked()
    signal menuRequested()
    signal markClicked()
    signal deleteClicked()

    width: ListView.view ? ListView.view.width : 400
    height: card.height + 8

    // Show an ink flash when picked
    function flash() { flashAnim.restart(); pickAnim.restart() }

    // Replay the card's enter animation after a delay when the panel opens
    function replay(delayMs) { enterAnim.stop(); enterAnim.delay = Math.max(0, delayMs); enterAnim.restart() }

    SequentialAnimation {
        id: enterAnim
        property int delay: 0
        PropertyAction { target: root; property: "appear"; value: 0 }
        PauseAnimation { duration: enterAnim.delay }
        NumberAnimation { target: root; property: "appear"; to: 1; duration: 380; easing.type: Easing.OutCubic }
    }

    Item {
        id: card
        // side margin so the tape, stack shadow and animations are not cut at the list edge
        x: 9
        width: parent.width - 18
        height: content.height + 28
        opacity: root.appear
        transform: Translate { y: (1 - root.appear) * 16 - root.lift * 3 }
        rotation: (1 - root.appear) * -1.6
        scale: (press.pressed ? 0.985 : 1) * root.pickScale
        Behavior on scale { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }

        // paper stack underneath (shows a bit more when selected)
        Rectangle {
            x: 2 + root.lift * 2; y: 3 + root.lift * 3
            width: parent.width; height: parent.height
            radius: Theme.cardRadius
            color: root.selected ? Theme.alpha(Theme.accent, 0.35) : Theme.stack
            Behavior on color { ColorAnimation { duration: 160 } }
        }

        // paper surface
        Rectangle {
            anchors.fill: parent
            radius: Theme.cardRadius
            color: Theme.sheet
            border.width: root.selected ? 1.5 : 1
            border.color: root.selected ? Theme.accent : Theme.edge
            Behavior on border.color { ColorAnimation { duration: 140 } }
        }

        // pinned marker: green tape stuck on the corner
        Rectangle {
            id: tape
            x: -6; y: 6
            width: 34; height: 12; radius: 2
            rotation: -38
            color: Theme.alpha(Theme.sage, 0.9)
            opacity: root.pinned ? 1 : 0
            scale: root.pinned ? 1 : 0.3
            Behavior on opacity { NumberAnimation { duration: 180 } }
            Behavior on scale { NumberAnimation { duration: 300; easing.type: Easing.OutBack; easing.overshoot: 2.5 } }
        }

        MouseArea {
            id: press
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            cursorShape: Qt.PointingHandCursor
            onPositionChanged: m => { const g = press.mapToGlobal(m.x, m.y); root.hoverMoved(g.x, g.y) }
            // left: paste, Ctrl+left: queue, right: menu
            onClicked: m => {
                if (m.button === Qt.RightButton) root.menuRequested()
                else if (m.modifiers & Qt.ControlModifier) root.markClicked()
                else root.pick(true)
            }
        }

        Item {
            id: content
            x: 16; y: 14
            width: parent.width - 32
            height: Math.max(body.item ? body.item.implicitHeight : 0, 22) + (footer.visible ? footer.height + 6 : 0)

            Loader {
                id: body
                width: parent.width - (root.kind === "image" ? 0 : 64)
                sourceComponent: root.kind === "image" ? imageView
                    : root.secret ? secretView
                    : root.hint === "color" ? colorView
                    : (root.hint === "url" || root.hint === "email") ? linkView
                    : root.hint === "code" ? codeView : textView
            }

            // bottom line: source app, folder, template mark
            Row {
                id: footer
                anchors { left: parent.left; bottom: parent.bottom }
                spacing: 6
                height: 18
                visible: srcLabel.text !== "" || root.tag !== "" || root.template
                Text {
                    id: srcLabel
                    anchors.verticalCenter: parent.verticalCenter
                    text: Store.on("show_source") ? Store.appName(root.source) : ""
                    color: Theme.pencil
                    font.family: Theme.sans
                    font.pixelSize: 11
                }
                Rectangle {
                    visible: root.tag !== ""
                    anchors.verticalCenter: parent.verticalCenter
                    height: 16; radius: 8
                    width: tagText.implicitWidth + 14
                    color: Theme.alpha(Theme.sage, 0.35)
                    Text { id: tagText; anchors.centerIn: parent; text: root.tag; color: Theme.ink; font.family: Theme.sans; font.pixelSize: 10; font.weight: Font.DemiBold }
                }
                Rectangle {
                    visible: root.template
                    anchors.verticalCenter: parent.verticalCenter
                    height: 16; radius: 8
                    width: tplText.implicitWidth + 14
                    color: Theme.alpha(Theme.tape, 0.6)
                    Text { id: tplText; anchors.centerIn: parent; text: Strings.t("templateNote"); color: Theme.ink; font.family: Theme.sans; font.pixelSize: 10; font.weight: Font.DemiBold }
                }
            }

            // top right: time, or actions when selected
            Item {
                anchors { right: parent.right; top: parent.top }
                width: 60; height: 22
                visible: root.kind !== "image" || root.hot

                Text {
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                    text: Store.ago(root.used)
                    color: Theme.pencil
                    font.family: Theme.sans
                    font.pixelSize: 12
                    opacity: root.hot ? 0 : 1
                    Behavior on opacity { NumberAnimation { duration: 140 } }
                }
                Row {
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter; rightMargin: -6 }
                    opacity: root.hot ? 1 : 0
                    enabled: root.hot
                    Behavior on opacity { NumberAnimation { duration: 140 } }
                    Rectangle {
                        visible: root.kind === "image"
                        width: 60; height: 28; radius: 14; color: Theme.sheet
                        anchors.verticalCenter: parent.verticalCenter
                        Row {
                            anchors.centerIn: parent
                            IconButton { icon: "pin"; size: 28; tint: root.pinned ? Theme.sage : Theme.pencil; onClicked: root.pinClicked() }
                            IconButton { icon: "trash"; size: 28; hoverTint: Theme.danger; onClicked: root.deleteClicked() }
                        }
                    }
                    IconButton { visible: root.kind !== "image"; icon: "pin"; size: 28; tint: root.pinned ? Theme.sage : Theme.pencil; onClicked: root.pinClicked() }
                    IconButton { visible: root.kind !== "image"; icon: "trash"; size: 28; hoverTint: Theme.danger; onClicked: root.deleteClicked() }
                }
            }
        }

        // paste queue number (peach circle) on the left edge
        Rectangle {
            x: -7; y: 10
            width: 22; height: 22; radius: 11
            color: Theme.accent
            border.width: 2; border.color: Theme.sheet
            scale: root.markNo > 0 ? 1 : 0
            visible: scale > 0
            Behavior on scale { NumberAnimation { duration: 260; easing.type: Easing.OutBack; easing.overshoot: 2.2 } }
            Text { anchors.centerIn: parent; text: root.markNo; color: Theme.sheet; font.family: Theme.sans; font.pixelSize: 11; font.weight: Font.Bold }
        }

        // Alt+number shortcut hint while Alt is held
        Rectangle {
            anchors { right: parent.right; bottom: parent.bottom; rightMargin: 8; bottomMargin: 8 }
            width: 22; height: 20; radius: 6
            color: Theme.alpha(Theme.tape, 0.95)
            opacity: root.showNumber && root.index < 9 ? 1 : 0
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: 120 } }
            Text { anchors.centerIn: parent; text: root.index + 1; color: Theme.ink; font.family: Theme.mono; font.pixelSize: 12; font.weight: Font.Bold }
        }

        // peach flash when picked
        Rectangle {
            id: flashRect
            anchors.fill: parent
            radius: Theme.cardRadius
            color: Theme.accent
            opacity: 0
            SequentialAnimation {
                id: flashAnim
                NumberAnimation { target: flashRect; property: "opacity"; to: 0.45; duration: 70 }
                NumberAnimation { target: flashRect; property: "opacity"; to: 0; duration: 300; easing.type: Easing.OutCubic }
            }
        }
    }

    // when pasting the card grows for a moment and settles
    SequentialAnimation {
        id: pickAnim
        NumberAnimation { target: root; property: "pickScale"; to: 1.025; duration: 80; easing.type: Easing.OutQuad }
        NumberAnimation { target: root; property: "pickScale"; to: 1; duration: 200; easing.type: Easing.OutBack }
    }

    // ---- content kinds ----

    Component {
        id: textView
        Item {
            implicitHeight: t.implicitHeight
            Text {
                id: t
                width: parent.width
                text: root.preview.replace(/^\s+/, "")
                textFormat: Text.PlainText    // copied HTML is shown as text, never rendered
                wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                maximumLineCount: 3
                elide: Text.ElideRight
                color: Theme.ink
                font.family: Theme.sans
                font.pixelSize: 14
                lineHeight: 1.2
            }
        }
    }

    Component {
        id: codeView
        Item {
            implicitHeight: t.implicitHeight
            Text {
                id: t
                width: parent.width
                // colored tokens come from the backend, already HTML-escaped
                text: root.rich !== "" ? root.rich : root.preview.replace(/^\s*\n/, "").replace(/\s+$/, "")
                textFormat: root.rich !== "" ? Text.StyledText : Text.PlainText
                wrapMode: Text.WrapAnywhere
                maximumLineCount: 4
                elide: Text.ElideRight
                color: Theme.ink
                font.family: Theme.mono
                font.pixelSize: 12
                lineHeight: 1.2
            }
        }
    }

    Component {
        id: colorView
        Row {
            spacing: 12
            Rectangle {
                width: 30; height: 30; radius: 15
                color: Store.cssColor(root.meta)
                border.width: 1; border.color: Theme.edge
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: root.meta
                textFormat: Text.PlainText
                color: Theme.ink
                font.family: Theme.mono
                font.pixelSize: 15; font.weight: Font.DemiBold
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: Store.colorAlt(root.meta)
                color: Theme.pencil
                font.family: Theme.mono
                font.pixelSize: 12
            }
        }
    }

    Component {
        id: secretView
        Column {
            spacing: 4
            Text {
                text: "••••••••••••"
                color: Theme.ink
                font.family: Theme.mono
                font.pixelSize: 15; font.letterSpacing: 2
            }
            Text {
                text: Strings.t("secret", Store.secretMinutes)
                color: Theme.danger
                font.family: Theme.sans
                font.pixelSize: 11
            }
        }
    }

    Component {
        id: linkView
        Item {
            implicitHeight: root.title !== "" ? 42 : 22
            // page title above the address when it is known
            Text {
                id: pageTitle
                visible: root.title !== ""
                anchors { left: parent.left; right: parent.right; top: parent.top }
                text: root.title
                textFormat: Text.PlainText
                elide: Text.ElideRight
                color: Theme.ink
                font.family: Theme.sans
                font.pixelSize: 14; font.weight: Font.DemiBold
            }
            Icon { id: linkIcon; name: root.hint === "email" ? "mail" : "link"; size: 14; color: Theme.accent; anchors.bottom: parent.bottom; anchors.bottomMargin: 4 }
            Text {
                anchors { left: linkIcon.right; leftMargin: 8; right: parent.right; verticalCenter: linkIcon.verticalCenter }
                text: root.preview.trim().replace(/^[a-z]+:\/\/(www\.)?/i, "")
                textFormat: Text.PlainText
                elide: Text.ElideMiddle
                color: Theme.ink
                font.family: Theme.sans
                font.pixelSize: root.title !== "" ? 12 : 14
                font.underline: true
            }
        }
    }

    Component {
        id: imageView
        Item {
            implicitHeight: root.imgW > 0 ? Math.max(70, Math.min(180, width * root.imgH / root.imgW)) : 140

            Image {
                id: pic
                anchors.fill: parent
                source: root.image
                fillMode: Image.PreserveAspectCrop
                sourceSize.width: 720
                asynchronous: true
                smooth: true
                visible: false
            }
            Rectangle { id: maskRect; anchors.fill: parent; radius: 8; visible: false; layer.enabled: true }
            Rectangle { anchors.fill: parent; radius: 8; color: Theme.stack; visible: pic.status !== Image.Ready }
            MultiEffect {
                anchors.fill: parent
                source: pic
                maskEnabled: true
                maskSource: maskRect
                opacity: pic.status === Image.Ready ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 300 } }
            }
        }
    }
}
