#!/usr/bin/env bash
# Generate and install the desktop launcher, app-menu entry, autostart entry
# and tray icon for the current user. All paths are derived from wherever this
# repository lives, so nothing is hardcoded.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

ICON_THEME_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
APPS_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
mkdir -p "$ICON_THEME_DIR" "$APPS_DIR" "$AUTOSTART_DIR" "$DESKTOP_DIR"

# Install the icon by name so the system tray renders it reliably.
cp "$PROJECT_DIR/assets/icon.png" "$ICON_THEME_DIR/tempteller.png"
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# $1 = output path, $2 = extra args passed to run-desktop.sh
make_entry() {
  cat > "$1" <<EOF
[Desktop Entry]
Type=Application
Name=TempTeller
Comment=Live system temperature & usage dashboard
Exec=$PROJECT_DIR/run-desktop.sh $2
Icon=tempteller
Terminal=false
Categories=System;Monitor;
StartupNotify=true
EOF
}

make_entry "$APPS_DIR/TempTeller.desktop" ""
make_entry "$DESKTOP_DIR/TempTeller.desktop" ""
make_entry "$AUTOSTART_DIR/TempTeller.desktop" "--tray"  # start hidden in tray on login

chmod +x "$DESKTOP_DIR/TempTeller.desktop"
gio set "$DESKTOP_DIR/TempTeller.desktop" metadata::trusted true 2>/dev/null || true
update-desktop-database "$APPS_DIR" 2>/dev/null || true

echo "Installed for $(whoami):"
echo "  app menu : $APPS_DIR/TempTeller.desktop"
echo "  desktop  : $DESKTOP_DIR/TempTeller.desktop"
echo "  autostart: $AUTOSTART_DIR/TempTeller.desktop  (starts hidden in tray)"
echo "  icon     : $ICON_THEME_DIR/tempteller.png"
echo "Done. Double-click the TempTeller icon on your desktop, or find it in the app menu."
