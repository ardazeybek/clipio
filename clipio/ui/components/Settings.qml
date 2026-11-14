// Settings page over the whole panel: an animated how-to guide, changeable shortcuts, feature switches, storage.
import QtQuick
import Clipio

Item {
    id: root
    property bool shown: false
    property string page: "guide"       // guide | keys | features | storage
    property string capturing: ""       // action whose new shortcut is being recorded
    signal closed()

    visible: fade > 0.001
    property real fade: shown ? 1 : 0
    Behavior on fade { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
    onShownChanged: { capturing = ""; if (shown) { flick.contentY = 0; Qt.callLater(() => keyCatcher.forceActiveFocus()) } }

    // guide entries: demo kind, shortcut action shown on the keycaps
    readonly property var guide: [
        { kind: "paste", action: "paste" }, { kind: "search", action: "" },
        { kind: "paste_clean", action: "paste_clean" }, { kind: "queue", action: "mark" },
        { kind: "menu", action: "menu" }, { kind: "convert", action: "menu" },
        { kind: "edit", action: "edit" }, { kind: "folders", action: "pin" },
        { kind: "templates", action: "" }, { kind: "secrets", action: "" },
        { kind: "quick_numbers", action: "" }, { kind: "app_filter", action: "" }
    ]
    readonly property var actionList: ["paste", "paste_clean", "copy", "menu", "edit", "mark", "pin", "delete", "next_tab", "prev_tab", "settings"]
    readonly property var featureList: ["clean_links", "detect_secrets", "templates", "code_colors", "show_source", "quick_numbers", "link_titles"]

    // Start recording a new shortcut for an action
    function capture(action) { capturing = action; keyCatcher.forceActiveFocus() }

    // Keys: record a shortcut, or Esc closes the page
    Item {
        id: keyCatcher
        focus: root.shown
        Keys.onPressed: e => {
            e.accepted = true
            if (root.capturing !== "") {
                if (e.key === Qt.Key_Escape) { root.capturing = ""; return }
                if (e.key === Qt.Key_Backspace && e.modifiers === Qt.NoModifier) { Store.setShortcut(root.capturing, ""); root.capturing = ""; return }
                const seq = Store.keySeq(e)
                if (seq === "") return        // only a modifier so far
                Store.setShortcut(root.capturing, seq)
                root.capturing = ""
                return
            }
            if (e.key === Qt.Key_Escape) root.closed()
            else if (e.key === Qt.Key_Tab) root.page = ["guide", "keys", "features", "storage"][(["guide", "keys", "features", "storage"].indexOf(root.page) + 1) % 4]
        }
    }

    // paper page
    Rectangle {
        anchors.fill: parent
        radius: Theme.radius
        color: Theme.paper
        border.width: 1; border.color: Theme.edge
        opacity: root.fade
        MouseArea { anchors.fill: parent; onClicked: keyCatcher.forceActiveFocus() }
    }

    Item {
        anchors.fill: parent
        opacity: root.fade
        transform: Translate { y: (1 - root.fade) * 18 }

        // title row
        Text {
            id: heading
            x: 22; y: 26
            text: Strings.t("settings")
            color: Theme.ink
            font.family: Theme.sans; font.pixelSize: 20; font.weight: Font.Bold
        }
        IconButton {
            anchors { right: parent.right; rightMargin: 14; verticalCenter: heading.verticalCenter }
            icon: "x"; size: 34
            tint: Theme.danger; hoverTint: Theme.danger; glow: Theme.danger
            onClicked: root.closed()
        }

        Tabs {
            id: tabs
            anchors { top: heading.bottom; topMargin: 12; left: parent.left; leftMargin: 12 }
            current: root.page
            tabs: [
                { key: "guide", label: Strings.t("tabGuide") }, { key: "keys", label: Strings.t("tabKeys") },
                { key: "features", label: Strings.t("tabFeatures") }, { key: "storage", label: Strings.t("tabStorage") }
            ]
            onPicked: key => { root.page = key; root.capturing = ""; flick.contentY = 0; keyCatcher.forceActiveFocus() }
        }

        Flickable {
            id: flick
            anchors { top: tabs.bottom; topMargin: 10; left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 18; rightMargin: 18; bottomMargin: 14 }
            contentHeight: pages.height + 20
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            Item {
                id: pages
                width: flick.width
                height: root.page === "guide" ? guideCol.height : root.page === "keys" ? keysCol.height
                      : root.page === "features" ? featCol.height : storeCol.height

                // ---- guide: one animated demo per feature ----
                Column {
                    id: guideCol
                    visible: root.page === "guide"
                    width: parent.width
                    spacing: 12
                    Text {
                        width: parent.width
                        text: Strings.t("guideIntro")
                        color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 13
                        wrapMode: Text.Wrap
                    }
                    Repeater {
                        model: root.guide
                        Rectangle {
                            required property var modelData
                            width: guideCol.width
                            height: gcol.implicitHeight + 24
                            radius: Theme.cardRadius
                            color: Theme.sheet
                            border.width: 1; border.color: Theme.edge
                            Column {
                                id: gcol
                                x: 12; y: 12
                                width: parent.width - 24
                                spacing: 8
                                Row {
                                    width: parent.width
                                    spacing: 8
                                    Text {
                                        width: parent.width - keyLbl.width - 8
                                        text: Strings.t("g_" + modelData.kind)
                                        color: Theme.ink; font.family: Theme.sans; font.pixelSize: 14; font.weight: Font.Bold
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        id: keyLbl
                                        text: modelData.action !== "" ? Store.keysOf(modelData.action) : ""
                                        color: Theme.accent; font.family: Theme.mono; font.pixelSize: 11; font.weight: Font.Bold
                                    }
                                }
                                GuideDemo {
                                    width: parent.width
                                    height: implicitHeight
                                    kind: modelData.kind
                                    keys: modelData.action !== "" ? Store.keysOf(modelData.action) : ""
                                    // only animate demos that are on screen
                                    playing: root.shown && root.page === "guide"
                                        && parent.parent.y + parent.parent.height > flick.contentY
                                        && parent.parent.y < flick.contentY + flick.height
                                }
                                Text {
                                    width: parent.width
                                    text: Strings.t("gd_" + modelData.kind)
                                    color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 12
                                    wrapMode: Text.Wrap; lineHeight: 1.15
                                }
                            }
                        }
                    }
                }

                // ---- shortcuts: click a key and press the new one ----
                Column {
                    id: keysCol
                    visible: root.page === "keys"
                    width: parent.width
                    spacing: 6
                    Text {
                        width: parent.width
                        text: Strings.t("keysIntro")
                        color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 13
                        wrapMode: Text.Wrap
                        bottomPadding: 4
                    }
                    Repeater {
                        model: root.actionList
                        Rectangle {
                            required property string modelData
                            readonly property bool rec: root.capturing === modelData
                            readonly property bool changed: Store.shortcuts[modelData] !== Store.defaultShortcuts[modelData]
                            width: keysCol.width; height: 44; radius: 10
                            color: rec ? Theme.alpha(Theme.accent, 0.14) : Theme.sheet
                            border.width: 1; border.color: rec ? Theme.accent : Theme.edge
                            Text {
                                x: 14; anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - keyBtn.width - 36
                                text: Strings.t("a_" + modelData)
                                elide: Text.ElideRight
                                color: Theme.ink; font.family: Theme.sans; font.pixelSize: 13; font.weight: Font.Medium
                            }
                            Rectangle {
                                id: keyBtn
                                anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                width: Math.max(70, kbt.implicitWidth + 20); height: 30; radius: 8
                                color: rec ? Theme.accent : (kma.containsMouse ? Theme.alpha(Theme.tape, 0.9) : Theme.paper)
                                border.width: 1; border.color: Qt.darker(Theme.edge, 1.1)
                                Behavior on color { ColorAnimation { duration: 140 } }
                                Text {
                                    id: kbt
                                    anchors.centerIn: parent
                                    text: rec ? Strings.t("pressKeys") : Store.keysOf(modelData)
                                    color: rec ? Theme.sheet : Theme.ink
                                    font.family: Theme.mono; font.pixelSize: 12; font.weight: Font.Bold
                                }
                                MouseArea { id: kma; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.capture(modelData) }
                            }
                            // a dot marks a changed shortcut
                            Rectangle { visible: changed;
                                anchors { right: keyBtn.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                width: 6
                                height: 6
                                radius: 3
                                color: Theme.accent }
                        }
                    }
                    Text {
                        width: parent.width
                        text: Strings.t("keysFixed")
                        color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 12
                        wrapMode: Text.Wrap
                        topPadding: 6
                    }
                    PaperButton { label: Strings.t("resetKeys"); onClicked: { Store.resetShortcuts(); keyCatcher.forceActiveFocus() } }
                }

                // ---- features: switch each one on or off ----
                Column {
                    id: featCol
                    visible: root.page === "features"
                    width: parent.width
                    spacing: 6
                    Repeater {
                        model: root.featureList
                        Rectangle {
                            required property string modelData
                            readonly property bool isOn: Store.on(modelData)
                            width: featCol.width
                            height: ftxt.implicitHeight + 24
                            radius: 10
                            color: Theme.sheet
                            border.width: 1; border.color: Theme.edge
                            Column {
                                id: ftxt
                                x: 14; anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - 86
                                spacing: 2
                                Text { width: parent.width; text: Strings.t("f_" + modelData); color: Theme.ink; font.family: Theme.sans; font.pixelSize: 13; font.weight: Font.DemiBold; wrapMode: Text.Wrap }
                                Text { width: parent.width; text: Strings.t("fd_" + modelData); color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 11; wrapMode: Text.Wrap }
                            }
                            // switch
                            Rectangle {
                                anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                                width: 44; height: 24; radius: 12
                                color: isOn ? Theme.sage : Theme.stack
                                Behavior on color { ColorAnimation { duration: 160 } }
                                Rectangle {
                                    x: isOn ? 22 : 2; y: 2
                                    width: 20; height: 20; radius: 10
                                    color: Theme.sheet
                                    Behavior on x { NumberAnimation { duration: 220; easing.type: Easing.OutBack; easing.overshoot: 1.8 } }
                                }
                            }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { Store.toggleFeature(modelData); keyCatcher.forceActiveFocus() } }
                        }
                    }
                }

                // ---- storage: retention and ignored apps ----
                Column {
                    id: storeCol
                    visible: root.page === "storage"
                    width: parent.width
                    spacing: 12
                    Text { width: parent.width; text: Strings.t("keepFor"); color: Theme.ink; font.family: Theme.sans; font.pixelSize: 14; font.weight: Font.Medium }
                    Row {
                        id: dayRow
                        width: parent.width
                        spacing: 6
                        Repeater {
                            model: [1, 3, 7, 14, 30]
                            PaperButton {
                                required property int modelData
                                width: (dayRow.width - dayRow.spacing * 4) / 5
                                label: Strings.t("days", modelData)
                                checked: Store.retentionDays === modelData
                                onClicked: Store.setRetention(modelData)
                            }
                        }
                    }
                    Text { width: parent.width; text: Strings.t("keepNote"); color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 12; wrapMode: Text.Wrap }
                    Text { width: parent.width; text: Strings.t("memory"); color: Theme.ink; font.family: Theme.sans; font.pixelSize: 14; font.weight: Font.Medium; topPadding: 6 }
                    Row {
                        id: memRow
                        width: parent.width
                        spacing: 6
                        Repeater {
                            model: [0, 1, 5, 30, 1440]
                            PaperButton {
                                required property int modelData
                                width: (memRow.width - memRow.spacing * 4) / 5
                                label: modelData === 0 ? Strings.t("memNow") : modelData === 1440 ? Strings.t("memAlways") : Strings.t("memMin", modelData)
                                checked: Store.panelKeep === modelData
                                onClicked: Store.setPanelKeep(modelData)
                            }
                        }
                    }
                    Text { width: parent.width; text: Strings.t("memNote"); color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 12; wrapMode: Text.Wrap }
                    Text { width: parent.width; text: Strings.t("ignored"); color: Theme.ink; font.family: Theme.sans; font.pixelSize: 14; font.weight: Font.Medium; topPadding: 6 }
                    Flow {
                        width: parent.width
                        spacing: 6
                        visible: Store.ignoreApps.length > 0
                        Repeater {
                            model: Store.ignoreApps
                            PaperButton {
                                required property string modelData
                                height: 28
                                label: Store.appName(modelData) + "  ✕"
                                onClicked: Store.setAppIgnored(modelData, false)
                            }
                        }
                    }
                    Text { width: parent.width; text: Strings.t("noneIgnored"); color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 12; wrapMode: Text.Wrap }
                    Text { width: parent.width; text: Strings.t("configNote"); color: Theme.pencil; font.family: Theme.sans; font.pixelSize: 12; wrapMode: Text.Wrap; topPadding: 6 }
                }
            }
        }
    }
}
