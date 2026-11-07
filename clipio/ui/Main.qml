// Clipio window: a frameless, transparent, always-on-top window that holds the panel.
import QtQuick
import QtQuick.Window
import Clipio
import "components"

Window {
    id: win

    readonly property int margin: 44     // room for the panel's shadow and tape
    readonly property rect panelRect: Qt.rect(panel.x, panel.y, panel.width, panel.height)

    title: "Clipio"
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
           | (Qt.platform.os === "windows" || Qt.platform.os === "osx" ? Qt.Tool : 0)
    visible: false
    width: panel.width + margin * 2
    height: panel.height + margin * 2
    // a fixed size also tells tiling window managers to float the window
    minimumWidth: width; maximumWidth: width
    minimumHeight: height; maximumHeight: height

    // close when another window gets focus
    onActiveChanged: if (!active && visible) Backend.focusLost()

    Panel {
        id: panel
        x: win.margin
        y: win.margin - 8
        height: Math.min(660, Math.max(420, Screen.desktopAvailableHeight - 140))
        shown: Backend.shown
        onCloseRequested: Backend.requestHide()
    }
}
