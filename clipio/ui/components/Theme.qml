// Theme: warm paper colors, fonts and shared sizes (single source of truth).
pragma Singleton
import QtQuick

QtObject {
    // paper surfaces
    readonly property color paper: "#F6EFE1"       // panel: old notebook paper
    readonly property color sheet: "#FFFCF5"       // card: clean note paper
    readonly property color edge: "#E4D8C2"        // paper edge
    readonly property color stack: "#E9DFCB"       // paper stack under a card
    readonly property color shadow: Qt.rgba(0.36, 0.27, 0.16, 0.24)

    // ink
    readonly property color ink: "#3D3530"
    readonly property color pencil: "#9A8E7E"

    // pastel accents
    readonly property color accent: "#E58F6F"      // peach (selection)
    readonly property color tape: "#F3D9A4"        // mustard tape
    readonly property color sage: "#9CC3A6"        // sage (pinned)
    readonly property color danger: "#D9695F"

    // fonts: the first installed family of each list wins (Linux, macOS, Windows)
    readonly property string sans: pick(["Nunito", "Quicksand", "Inter", "SF Pro Text", "Segoe UI",
                                         "Helvetica Neue", "Noto Sans", "DejaVu Sans"], "sans-serif")
    readonly property string mono: pick(["JetBrains Mono", "CaskaydiaCove", "Fira Code", "SF Mono",
                                         "Menlo", "Cascadia Mono", "Consolas", "DejaVu Sans Mono"], "monospace")

    // Return the first installed candidate (prefix match), otherwise the fallback
    function pick(candidates, fallback) {
        const have = Qt.fontFamilies()
        const lower = have.map(f => f.toLowerCase())
        for (const c of candidates) {
            const i = lower.findIndex(f => f.startsWith(c.toLowerCase()))
            if (i >= 0) return have[i]
        }
        return fallback
    }

    readonly property int radius: 22
    readonly property int cardRadius: 14

    // Return a copy of a color with a different opacity
    function alpha(c, a) { return Qt.rgba(c.r, c.g, c.b, a) }
}
