#!/usr/bin/env bash
# Clipio kurulumu: komutu, Quickshell yapılandırmasını, masaüstü girdisini ve simgeyi kullanıcı klasörlerine bağlar.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
QS_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/quickshell"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

# Gerekli bir komut yoksa uyar ve eksik say
missing=0
need() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Eksik / missing: $1 ($2)"
        missing=1
    fi
}

# bağımlılık denetimi
need python3 "Python 3.11+"
need wl-copy "wl-clipboard"
need wl-paste "wl-clipboard"
need hyprctl "Hyprland"
if ! command -v quickshell >/dev/null 2>&1 && ! command -v qs >/dev/null 2>&1; then
    echo "Eksik / missing: quickshell (Quickshell)"
    missing=1
fi
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
    echo "Python 3.11 veya üstü gerekli / Python 3.11+ required"
    missing=1
fi
[ "$missing" -eq 0 ] || { echo "Önce eksikleri kur / install the missing tools first."; exit 1; }

# komut: ~/.local/bin/clipio
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/clipio" <<EOF
#!/usr/bin/env bash
exec python3 -I "$ROOT/cli/clipio.py" "\$@"
EOF
chmod +x "$BIN_DIR/clipio"

# Quickshell yapılandırması: ~/.config/quickshell/clipio -> ui/
mkdir -p "$QS_DIR"
if [ -e "$QS_DIR/clipio" ] && [ ! -L "$QS_DIR/clipio" ]; then
    echo "$QS_DIR/clipio zaten var ve bağlantı değil; dokunmadım / exists and is not a symlink, left untouched."
    exit 1
fi
ln -sfn "$ROOT/ui" "$QS_DIR/clipio"

# masaüstü girdisi ve simge
mkdir -p "$APP_DIR" "$ICON_DIR"
install -m 644 "$ROOT/ui/assets/clipio.svg" "$ICON_DIR/clipio-paper.svg"
cat > "$APP_DIR/clipio.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Clipio
GenericName=Clipboard History
Comment=Paper-themed clipboard history for Hyprland
Exec=$BIN_DIR/clipio toggle
Icon=clipio-paper
Terminal=false
Categories=Utility;
Keywords=clipboard;pano;copy;paste;history;
EOF

echo "Clipio kuruldu / installed: $BIN_DIR/clipio"
case ":$PATH:" in *":$BIN_DIR:"*) ;; *) echo "Not: $BIN_DIR PATH içinde değil / is not on your PATH." ;; esac
cat <<EOF

Hyprland ayarına ekle / add to your Hyprland config (hyprland.conf):

    exec-once = $BIN_DIR/clipio start
    bind = SUPER, V, exec, $BIN_DIR/clipio toggle

Sonra / then: $BIN_DIR/clipio start
EOF
