// Boş liste görünümü: süzülüp hafifçe sallanan logo, altında gölgesi ve kısa bir cümle; belirirken zıplar.
import QtQuick

Item {
    id: root
    property string title: ""
    property string sub: ""

    // görünür olunca içeriği aşağıdan zıplatarak getir
    onVisibleChanged: if (visible) enter.restart()
    ParallelAnimation {
        id: enter
        NumberAnimation { target: col; property: "scale"; from: 0.85; to: 1; duration: 460; easing.type: Easing.OutBack; easing.overshoot: 1.8 }
        NumberAnimation { target: col; property: "anchors.verticalCenterOffset"; from: 18; to: 0; duration: 460; easing.type: Easing.OutCubic }
    }

    Column {
        id: col
        anchors.centerIn: parent
        spacing: 12

        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 84; height: 96

            // yerdeki gölge: logo yükseldikçe küçülür
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 88
                width: 48 - logo.lift * 1.5; height: 6; radius: 3
                color: Theme.alpha(Theme.ink, 0.08)
            }
            Image {
                id: logo
                property real lift: 0
                x: 2; y: 4 - lift
                width: 80; height: 80
                source: Qt.resolvedUrl("../assets/clipio.svg")
                sourceSize: Qt.size(240, 240)
                smooth: true
                SequentialAnimation on lift {
                    loops: Animation.Infinite
                    running: root.visible
                    NumberAnimation { to: 7; duration: 1600; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 0; duration: 1600; easing.type: Easing.InOutSine }
                }
                SequentialAnimation on rotation {
                    loops: Animation.Infinite
                    running: root.visible
                    NumberAnimation { to: 3; duration: 2100; easing.type: Easing.InOutSine }
                    NumberAnimation { to: -3; duration: 2100; easing.type: Easing.InOutSine }
                }
            }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.title
            color: Theme.ink
            font.family: Theme.sans
            font.pixelSize: 15; font.weight: Font.Bold
        }
        Text {
            visible: root.sub !== ""
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.sub
            color: Theme.pencil
            font.family: Theme.sans
            font.pixelSize: 13
        }
    }
}
