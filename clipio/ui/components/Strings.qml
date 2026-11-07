// Interface texts (English).
pragma Singleton
import QtQuick

QtObject {
    readonly property var texts: ({
        all: "All", text: "Text", image: "Images", pinned: "Pinned",
        search: "Search…", paused: "Recording paused",
        empty: "Nothing here yet", emptySub: "Copy something and it shows up here.",
        noMatch: "No matches",
        clearTitle: "Clear everything?", clearSub: "All copied items will be deleted. Pinned ones stay.",
        cancel: "Cancel", clearYes: "Yes, delete",
        settings: "Settings", keepFor: "How long should copies be kept?", days: "%1 days", day1: "1 day",
        keepNote: "Older items are deleted. Pinned items are never deleted.", done: "Done",
        now: "now", min: "m", hour: "h", day: "d"
    })

    // Return the text for a key; %1 is replaced by arg
    function t(key, arg) {
        if (key === "days" && arg === 1) return texts.day1
        const s = texts[key] !== undefined ? texts[key] : key
        return arg === undefined ? s : s.replace("%1", arg)
    }
}
