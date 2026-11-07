// Clipio arayüz kökü: IPC ile aç/kapa, odaktaki monitörde tam ekran katman penceresi içinde paneli gösterir.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "components"

ShellRoot {
    id: root

    property bool shown: false
    property string targetScreen: ""

    // Odaktaki monitörü bulup paneli aç
    function show() {
        targetScreen = Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : Quickshell.screens[0].name
        shown = true
    }
    function hide() { shown = false }

    IpcHandler {
        target: "clipio"
        function toggle(): void { root.shown ? root.hide() : root.show() }
        function open(): void { root.show() }
        function close(): void { root.hide() }
    }

    onShownChanged: if (!shown) Store.watching = false

    Variants {
        model: Quickshell.screens

        PanelWindow {
            id: win
            required property var modelData
            readonly property bool isTarget: root.targetScreen === modelData.name

            screen: modelData
            visible: isTarget && (root.shown || panel.open > 0.001)
            color: "transparent"
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "clipio"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: root.shown && isTarget ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

            // panel dışına tıklayınca kapat (perde yok, arka plan olduğu gibi görünür)
            MouseArea { anchors.fill: parent; onClicked: root.hide() }

            Panel {
                id: panel
                // sürüklenince kaydırma payı kadar ortadan uzaklaşır
                x: (parent.width - width) / 2 + dragX
                y: (parent.height - height) / 2 - 24 + dragY
                shown: root.shown && win.isTarget
                onCloseRequested: root.hide()
            }
        }
    }
}
