// In-panel paper dialog: covers the panel with paper color and shows its content on a note card.
import QtQuick
import QtQuick.Effects

Item {
    id: root
    property bool shown: false
    property string title: ""
    default property alias content: body.data
    signal dismissed()

    // on open the tape drops in and sticks with a twist
    onShownChanged: if (shown) tapeAnim.restart()
    SequentialAnimation {
        id: tapeAnim
        PropertyAction { target: dtape; property: "opacity"; value: 0 }
        PauseAnimation { duration: 110 }
        ParallelAnimation {
            NumberAnimation { target: dtape; property: "opacity"; to: 1; duration: 140 }
            NumberAnimation { target: dtape; property: "scale"; from: 1.5; to: 1; duration: 380; easing.type: Easing.OutBack; easing.overshoot: 1.6 }
            NumberAnimation { target: dtape; property: "rotation"; from: 14; to: 2; duration: 460; easing.type: Easing.OutBack; easing.overshoot: 2 }
        }
    }

    visible: fade > 0.001
    property real fade: shown ? 1 : 0
    Behavior on fade { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

    // backdrop: closes on click and keeps clicks from reaching the panel
    Rectangle {
        anchors.fill: parent
        radius: Theme.radius
        color: Theme.alpha(Theme.paper, 0.82)
        opacity: root.fade
        MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: root.dismissed() }
    }

    Item {
        id: sheet
        anchors.centerIn: parent
        width: Math.min(parent.width - 48, 392)
        height: col.implicitHeight + 44
        opacity: root.fade
        scale: 0.92 + 0.08 * pop
        property real pop: root.shown ? 1 : 0
        Behavior on pop { NumberAnimation { duration: root.shown ? 340 : 140; easing.type: root.shown ? Easing.OutBack : Easing.InCubic } }

        RectangularShadow { anchors.fill: face; radius: Theme.cardRadius; blur: 30; offset: Qt.vector2d(0, 10); color: Theme.shadow }
        Rectangle { x: 4; y: 5; width: face.width; height: face.height; radius: Theme.cardRadius; color: Theme.stack }
        Rectangle {
            id: face
            anchors.fill: parent
            radius: Theme.cardRadius
            color: Theme.sheet
            border.width: 1; border.color: Theme.edge
            MouseArea { anchors.fill: parent }   // clicks inside the card must not reach the backdrop
        }
        Rectangle {
            id: dtape
            anchors.horizontalCenter: parent.horizontalCenter
            y: -8; width: 70; height: 18; radius: 3; rotation: 2
            color: Theme.alpha(Theme.tape, 0.9)
        }

        Column {
            id: col
            x: 22; y: 24
            width: parent.width - 44
            spacing: 16
            Text {
                width: parent.width
                text: root.title
                color: Theme.ink
                font.family: Theme.sans
                font.pixelSize: 16; font.weight: Font.Bold
                wrapMode: Text.Wrap
            }
            Column { id: body; width: parent.width; spacing: 16 }
        }
    }
}
