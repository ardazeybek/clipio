# clipio/ui/components/
QML components of the panel.

- `qmldir` — singleton and component registrations
- `Theme.qml` — paper colors, font choice, sizes (single source of truth)
- `Strings.qml` — interface texts
- `Store.qml` — reads the `Backend` state, filters it (All/Text/Images/Pinned), updates the ListModel by differences, forwards actions
- `Panel.qml` — main panel: paper page, search with pause/clear/settings, tabs, list, clear and settings dialogs, keyboard, open animation; dragging moves the window
- `ClipCard.qml` — one note card: content by kind, time, pin/delete on hover, animations
- `Tabs.qml` — text tabs with a sliding tape line
- `EmptyState.qml` — empty list view (floating logo)
- `Dialog.qml` — in-panel paper dialog (backdrop + note card)
- `PaperButton.qml` — paper button: filled, plain or selected
- `Icon.qml` — tints an SVG icon
- `IconButton.qml` — round icon button
