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
        now: "now", min: "m", hour: "h", day: "d",
        // card menu
        menu: "What should Clipio do?", pasteClean: "Paste cleaned", pasteCleanSub: "no tracking, tidy spaces",
        copyOnly: "Copy only", edit: "Edit, then paste", queueAdd: "Add to paste queue", queueRemove: "Remove from queue",
        convert: "Convert", folder: "Folder", folderHint: "New folder…", noFolder: "No folder",
        ocr: "Read text from image", ocrMissing: "Install tesseract to read text from images",
        ignoreApp: "Don't save copies from %1", reading: "Reading the image…", noText: "No text found in the image",
        // edit
        editTitle: "Edit before pasting", pasteIt: "Paste", copyIt: "Copy",
        // queue
        queued: "%1 in the paste queue · Enter pastes them in order", queueLeft: "%1 left · run `clipio next` or press Enter",
        clearQueue: "Clear",
        // card details
        secret: "Hidden secret · deleted after %1 min", templateNote: "template",
        // settings
        ignored: "Not saved from these apps", noneIgnored: "Password managers are always skipped.",
        // conversions
        upper: "UPPERCASE", lower: "lowercase", title: "Title Case", clean: "Clean up", join_lines: "Join lines",
        json_pretty: "Format JSON", json_min: "Minify JSON", base64_encode: "Base64 encode",
        base64_decode: "Base64 decode", url_encode: "URL encode", url_decode: "URL decode",
        hex_to_rgb: "HEX → RGB", rgb_to_hex: "RGB → HEX",
        // settings page
        tabGuide: "How to", tabKeys: "Shortcuts", tabFeatures: "Features", tabStorage: "Storage",
        memory: "Keep the panel ready after closing?", memNow: "Free at once", memMin: "%1 min", memAlways: "Always",
        memNote: "Clipio keeps recording in the background with little memory. The panel opens a bit slower once it was freed.",
        configNote: "Everything here is also saved in config.toml, so you can edit it by hand too.",
        guideIntro: "Every feature in a few seconds. The little animations show what happens; the keys on the right are your current shortcuts.",
        g_paste: "Pick and paste", gd_paste: "Open Clipio, move with ↑ ↓ and press the key. Clipio closes and pastes into the app you were using. A click works too.",
        g_search: "Find anything", gd_search: "Just start typing. Cards that don't match fade away.",
        g_paste_clean: "Paste cleaned", gd_paste_clean: "Removes tracking parts like utm_ and fbclid from links and tidies extra spaces before pasting.",
        g_queue: "Paste queue", gd_queue: "Mark several cards (or Ctrl + click them). They get numbers. Enter pastes the first; bind `clipio next` to a key to paste the rest in order.",
        g_menu: "Card menu", gd_menu: "Right-click a card for everything else: edit, convert, folder, read text from an image, or stop saving an app.",
        g_convert: "Convert text", gd_convert: "From the menu: UPPER/lower case, JSON, Base64, URL and HEX ↔ RGB. The result becomes a new card.",
        g_edit: "Edit before pasting", gd_edit: "Change the text first, then paste it. Ctrl + Enter pastes from the editor.",
        g_folders: "Pins and folders", gd_folders: "Pin what you reuse; pinned cards are never deleted. Put them in folders from the menu and pick a folder in the Pinned tab.",
        g_templates: "Templates", gd_templates: "Pinned text with {date}, {time}, {datetime}, {weekday} or {clipboard} is filled in when you paste it.",
        g_secrets: "Secrets hide themselves", gd_secrets: "Passwords, keys, tokens and card numbers show as dots and are deleted after a few minutes. Password managers are never saved.",
        g_quick_numbers: "Quick numbers", gd_quick_numbers: "Hold Alt to see numbers on the first nine cards; Alt + number pastes that card at once.",
        g_app_filter: "Filter by app", gd_app_filter: "Every card shows where it came from. Type @ and the app name, e.g. @firefox.",
        keysIntro: "Click a key, then press the new combination. Backspace puts the default back, Esc cancels.",
        keysFixed: "Arrows, Page Up/Down and Esc always work. Alt + 1…9 pastes the first nine cards.",
        pressKeys: "Press keys…", resetKeys: "Reset all shortcuts",
        a_paste: "Paste the selected card", a_paste_clean: "Paste it cleaned", a_copy: "Copy without pasting",
        a_menu: "Open the card menu", a_edit: "Edit, then paste", a_mark: "Add to the paste queue",
        a_pin: "Pin or unpin", a_delete: "Delete the card", a_next_tab: "Next tab", a_prev_tab: "Previous tab",
        a_settings: "Open settings",
        f_clean_links: "Clean copied links", fd_clean_links: "Removes utm_, fbclid, gclid and other trackers when you copy a link.",
        f_detect_secrets: "Hide secrets", fd_detect_secrets: "Passwords, keys and card numbers become dots and are deleted after 5 minutes.",
        f_templates: "Fill templates", fd_templates: "{date}, {time}, {clipboard}… in pinned cards are filled when pasted.",
        f_code_colors: "Color code", fd_code_colors: "Keywords, strings and comments in code cards get colors.",
        f_show_source: "Show the source app", fd_show_source: "Each card shows which app it was copied from.",
        f_quick_numbers: "Alt + number", fd_quick_numbers: "Alt + 1…9 pastes one of the first nine cards.",
        f_link_titles: "Page titles for links", fd_link_titles: "Shows the title of a copied web page. Clipio visits the link to read it, so it is off by default."
    })

    // Return the text for a key; %1 is replaced by arg
    function t(key, arg) {
        if (key === "days" && arg === 1) return texts.day1
        const s = texts[key] !== undefined ? texts[key] : key
        return arg === undefined ? s : s.replace("%1", arg)
    }
}
