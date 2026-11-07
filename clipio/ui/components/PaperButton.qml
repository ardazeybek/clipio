// Paper button: filled (main action) or plain; can also show a selected state (settings options).
import QtQuick

Rectangle {
    id: root
    property string label: ""
    property color fill: Theme.accent
    property bool solid: false
    property bool checked: false
    signal clicked()

    // short bounce when it becomes selected
    onCheckedChanged: if (checked) popAnim.restart()
    SequentialAnimation {
        id: popAnim
        NumberAnimation { target: lbl; property: "scale"; to: 1.15; duration: 100; easing.type: Easing.OutQuad }
        NumberAnimation { target: lbl; property: "scale"; to: 1; duration: 280; easing.type: Easing.OutBack; easing.overshoot: 2.4 }
    }

    implicitWidth: lbl.implicitWidth + (solid ? 32 : 24)
    implicitHeight: 36
    radius: 10
    color: solid ? (mouse.containsMouse ? Qt.darker(fill, 1.08) : fill)
        : checked ? Theme.alpha(Theme.tape, 0.9)
        : (mouse.containsMouse ? Theme.alpha(Theme.ink, 0.06) : "transparent")
    border.width: solid ? 0 : 1
    border.color: checked ? Qt.darker(Theme.tape, 1.15) : Theme.edge
    scale: mouse.pressed ? 0.95 : 1
    Behavior on color { ColorAnimation { duration: 140 } }
    Behavior on scale { NumberAnimation { duration: 110 } }

    Text {
        id: lbl
        anchors.centerIn: parent
        text: root.label
        color: root.solid ? Theme.sheet : Theme.ink
        font.family: Theme.sans
        font.pixelSize: 14
        font.weight: root.solid || root.checked ? Font.Bold : Font.Medium
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
