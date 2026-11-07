// Simge: icons/ klasöründeki beyaz SVG'yi istenen renge boyar.
import QtQuick
import QtQuick.Effects

Item {
    id: root
    property string name: ""
    property color color: Theme.pencil
    property real size: 16

    implicitWidth: size
    implicitHeight: size

    Image {
        id: img
        anchors.fill: parent
        source: root.name ? Qt.resolvedUrl("../icons/" + root.name + ".svg") : ""
        sourceSize: Qt.size(root.size * 3, root.size * 3)
        smooth: true
        visible: false
    }
    MultiEffect {
        anchors.fill: img
        source: img
        colorization: 1.0
        colorizationColor: root.color
        Behavior on colorizationColor { ColorAnimation { duration: 160 } }
    }
}
