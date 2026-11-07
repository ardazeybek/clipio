// Tema: sıcak kağıt görünümü renkleri, yazı tipleri ve ortak ölçüler (tek kaynak).
pragma Singleton
import QtQuick
import Quickshell

Singleton {
    // kağıt yüzeyler
    readonly property color paper: "#F6EFE1"       // panel: eski defter kağıdı
    readonly property color sheet: "#FFFCF5"       // kart: temiz not kağıdı
    readonly property color edge: "#E4D8C2"        // kağıt kenarı
    readonly property color stack: "#E9DFCB"       // kartın altındaki kağıt yığını
    readonly property color shadow: Qt.rgba(0.36, 0.27, 0.16, 0.24)

    // mürekkep
    readonly property color ink: "#3D3530"
    readonly property color pencil: "#9A8E7E"

    // pastel vurgular
    readonly property color accent: "#E58F6F"      // şeftali (seçim)
    readonly property color tape: "#F3D9A4"        // hardal bant
    readonly property color sage: "#9CC3A6"        // adaçayı (sabit)
    readonly property color danger: "#D9695F"

    // yazı tipleri: listedeki ilk kurulu aileyi seçer
    readonly property string sans: pick(["Nunito", "Quicksand", "Inter", "Noto Sans", "DejaVu Sans"], "sans-serif")
    readonly property string mono: pick(["JetBrains Mono", "CaskaydiaCove", "Fira Code", "DejaVu Sans Mono"], "monospace")

    // Adayların ilk kurulu olanını (ön ek eşleşmesiyle) döndür, yoksa yedeği
    function pick(candidates, fallback) {
        const have = Qt.fontFamilies().map(f => f.toLowerCase())
        for (const c of candidates)
            if (have.some(f => f.startsWith(c.toLowerCase()))) return have.find(f => f.startsWith(c.toLowerCase()))
        return fallback
    }

    readonly property int radius: 22
    readonly property int cardRadius: 14

    // Rengin şeffaflığını değiştirilmiş kopyasını döndür
    function alpha(c, a) { return Qt.rgba(c.r, c.g, c.b, a) }
}
