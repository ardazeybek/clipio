// Yuvarlak simge butonu: üzerine gelince kağıt lekesi ve isteğe bağlı dönme, tıklanınca zıplar; simge değişince yumuşakça döner.
import QtQuick

Item {
    id: root
    property string icon: ""
    property color tint: Theme.pencil
    property color hoverTint: Theme.ink
    property color glow: Theme.ink
    property real size: 30
    property real hoverSpin: 0          // üzerine gelince dönme açısı (ör. ayar dişlisi)
    property alias hovered: mouse.containsMouse
    signal clicked()

    implicitWidth: size
    implicitHeight: size
    scale: mouse.pressed ? 0.86 : (mouse.containsMouse ? 1.06 : 1.0)
    Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutBack; easing.overshoot: 2 } }

    // Tıklamada kısa zıplama oynat
    function bump() { bumpAnim.restart() }

    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: Theme.alpha(root.glow, mouse.containsMouse ? 0.08 : 0)
        Behavior on color { ColorAnimation { duration: 140 } }
    }
    Icon {
        id: ico
        anchors.centerIn: parent
        name: root.icon
        size: root.size * 0.5
        color: mouse.containsMouse ? root.hoverTint : root.tint
        rotation: mouse.containsMouse ? root.hoverSpin : 0
        Behavior on rotation { NumberAnimation { duration: 420; easing.type: Easing.OutBack } }
    }

    // simge adı değişince (duraklat ↔ sürdür) küçülüp dönerek yenisi belirir
    onIconChanged: swapAnim.restart()
    SequentialAnimation {
        id: swapAnim
        NumberAnimation { target: ico; property: "scale"; from: 0.4; to: 1; duration: 320; easing.type: Easing.OutBack; easing.overshoot: 2.2 }
    }
    SequentialAnimation {
        id: bumpAnim
        NumberAnimation { target: ico; property: "scale"; to: 1.3; duration: 90; easing.type: Easing.OutQuad }
        NumberAnimation { target: ico; property: "scale"; to: 1; duration: 260; easing.type: Easing.OutBack; easing.overshoot: 2.5 }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: { root.bump(); root.clicked() }
    }
}
