// Sekmeler: düz yazı sekmeleri; seçilinin altında kayan bant çizgisi, seçilen yazı zıplar.
import QtQuick

Item {
    id: root
    property var tabs: []           // [{key, label}]
    property string current: "all"
    property Item cur: null
    signal picked(string key)

    implicitHeight: 30
    implicitWidth: row.implicitWidth

    // seçili sekmenin altındaki bant
    Rectangle {
        y: root.height - 9
        height: 7; radius: 3.5
        x: root.cur ? root.cur.x + 6 : 0
        width: root.cur ? root.cur.width - 12 : 0
        color: Theme.tape
        rotation: -1
        Behavior on x { NumberAnimation { duration: 300; easing.type: Easing.OutBack; easing.overshoot: 1.2 } }
        Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutBack; easing.overshoot: 1.2 } }
    }

    Row {
        id: row
        Repeater {
            model: root.tabs
            delegate: Item {
                id: tab
                required property var modelData
                readonly property bool active: modelData.key === root.current
                width: lbl.implicitWidth + 22
                height: root.height
                onActiveChanged: if (active) { root.cur = tab; pop.restart() }
                Component.onCompleted: if (active) root.cur = tab

                // seçilince yazı hafifçe zıplar
                SequentialAnimation {
                    id: pop
                    NumberAnimation { target: lbl; property: "scale"; to: 1.12; duration: 90; easing.type: Easing.OutQuad }
                    NumberAnimation { target: lbl; property: "scale"; to: 1; duration: 280; easing.type: Easing.OutBack; easing.overshoot: 2.4 }
                }
                Text {
                    id: lbl
                    anchors.centerIn: parent
                    text: tab.modelData.label
                    font.family: Theme.sans
                    font.pixelSize: 14
                    font.weight: tab.active ? Font.Bold : Font.Medium
                    color: tab.active || mouse.containsMouse ? Theme.ink : Theme.pencil
                    Behavior on color { ColorAnimation { duration: 150 } }
                }
                MouseArea {
                    id: mouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.picked(tab.modelData.key)
                }
            }
        }
    }
}
