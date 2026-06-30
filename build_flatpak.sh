#!/bin/bash

# Exit on error
set -e

# Disable verbose output for cleaner progress reporting
# set -x

# Function to detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    elif [ -f /etc/redhat-release ]; then
        # More specific check for RHEL-based systems
        if grep -q "Rocky Linux" /etc/redhat-release; then
            DISTRO="rocky"
        elif grep -q "AlmaLinux" /etc/redhat-release; then
            DISTRO="alma"
        else
            DISTRO="rhel"
        fi
    else
        DISTRO="unknown"
    fi
    echo $DISTRO
}

# Function to detect desktop environment
detect_desktop() {
    if [ -n "$XDG_CURRENT_DESKTOP" ]; then
        DESKTOP=$XDG_CURRENT_DESKTOP
    elif [ -n "$DESKTOP_SESSION" ]; then
        DESKTOP=$DESKTOP_SESSION
    else
        # Try to detect using ps
        if pgrep -x "cinnamon" > /dev/null; then
            DESKTOP="Cinnamon"
        elif pgrep -x "gnome-shell" > /dev/null; then
            DESKTOP="GNOME"
        elif pgrep -x "plasmashell" > /dev/null; then
            DESKTOP="KDE"
        elif pgrep -x "xfce4-session" > /dev/null || pgrep -x "xfwm4" > /dev/null; then
            DESKTOP="XFCE"
        elif pgrep -x "Hyprland" > /dev/null; then
            DESKTOP="Hyprland"
        else
            DESKTOP="unknown"
        fi
    fi
    
    # Convert to uppercase for easier comparison
    DESKTOP_UPPER=$(echo "$DESKTOP" | tr '[:lower:]' '[:upper:]')
    
    # Check for XFCE in different formats
    if [[ "$DESKTOP_UPPER" == *"XFCE"* ]]; then
        DESKTOP="XFCE"
    # Check for Hyprland in different formats
    elif [[ "$DESKTOP_UPPER" == *"HYPRLAND"* ]]; then
        DESKTOP="Hyprland"
    fi
    
    echo $DESKTOP
}

# Function to apply enhanced Fedora Cinnamon icon fixes
fix_fedora_cinnamon_icon() {
    echo "===== Applying Fedora Cinnamon Icon Fixes ====="
    
    # 1. First, find existing icons we can use
    echo "Locating existing Calendifier icons..."
    ICON_SOURCE=""
    
    # Check exported flatpak icon - dynamically find paths based on installation
    FLATPAK_EXPORTS=$(find ~/.local/share/flatpak/exports/share/icons -name "*calendifier*.png" 2>/dev/null | head -1)
    FLATPAK_APP_ICONS=$(find ~/.local/share/flatpak/app/com.calendifier.Calendar -name "*calendar*.png" 2>/dev/null | head -1)
    LOCAL_ICON=$(find ~/.local/share/icons -name "*calendifier*.png" 2>/dev/null | head -1)
    SOURCE_ICON_128="$SOURCE_DIR/assets/calendar_icon_128x128.png"
    SOURCE_ICON="$SOURCE_DIR/assets/calendar_icon.png"
    
    if [ -n "$FLATPAK_EXPORTS" ]; then
        ICON_SOURCE="$FLATPAK_EXPORTS"
        echo "Found icon in Flatpak exports"
    elif [ -n "$FLATPAK_APP_ICONS" ]; then
        ICON_SOURCE="$FLATPAK_APP_ICONS"
        echo "Found icon in Flatpak app directory"
    elif [ -n "$LOCAL_ICON" ]; then
        ICON_SOURCE="$LOCAL_ICON"
        echo "Found icon in local icons directory"
    elif [ -f "$SOURCE_ICON_128" ]; then
        ICON_SOURCE="$SOURCE_ICON_128"
        echo "Using source directory 128x128 icon"
    elif [ -f "$SOURCE_ICON" ]; then
        ICON_SOURCE="$SOURCE_ICON"
        echo "Using source directory icon"
    else
        # Extract from the flatpak as last resort
        echo "No existing icon found, extracting from Flatpak..."
        mkdir -p /tmp/calendifier-fix
        flatpak run --command=sh com.calendifier.Calendar -c "find /app -name '*calendar*.png' -exec cp {} /tmp/calendifier-fix/icon.png \; -quit" || true
        
        if [ -f /tmp/calendifier-fix/icon.png ]; then
            ICON_SOURCE="/tmp/calendifier-fix/icon.png"
            echo "Extracted icon from Flatpak"
        else
            echo "WARNING: Could not find or extract any icons, icon may be missing in menu."
            return 1
        fi
    fi
    
    # 2. Create all the necessary icon directories
    echo "Creating icon directories..."
    mkdir -p ~/.icons
    mkdir -p ~/.local/share/icons/hicolor/16x16/apps
    mkdir -p ~/.local/share/icons/hicolor/22x22/apps
    mkdir -p ~/.local/share/icons/hicolor/24x24/apps
    mkdir -p ~/.local/share/icons/hicolor/32x32/apps
    mkdir -p ~/.local/share/icons/hicolor/48x48/apps
    mkdir -p ~/.local/share/icons/hicolor/64x64/apps
    mkdir -p ~/.local/share/icons/hicolor/128x128/apps
    mkdir -p ~/.local/share/icons/hicolor/256x256/apps
    
    # 3. Copy the icon to all standard locations
    echo "Copying icon to standard locations..."
    cp "$ICON_SOURCE" ~/.icons/com.calendifier.Calendar.png
    cp "$ICON_SOURCE" ~/.local/share/icons/hicolor/128x128/apps/com.calendifier.Calendar.png
    cp "$ICON_SOURCE" ~/.local/share/icons/hicolor/256x256/apps/com.calendifier.Calendar.png
    
    # Also copy with alternate names that Cinnamon might be looking for
    cp "$ICON_SOURCE" ~/.local/share/icons/hicolor/128x128/apps/calendifier.png
    cp "$ICON_SOURCE" ~/.icons/calendifier.png
    
    # 4. Fix the desktop file
    echo "Fixing desktop file..."
    if [ -f ~/.local/share/applications/com.calendifier.Calendar.desktop ]; then
        # Make backup
        cp ~/.local/share/applications/com.calendifier.Calendar.desktop ~/.local/share/applications/com.calendifier.Calendar.desktop.bak
        
        # Change to simple icon name (more reliable)
        sed -i "s|Icon=.*|Icon=com.calendifier.Calendar|g" ~/.local/share/applications/com.calendifier.Calendar.desktop
        
        echo "Desktop file updated to use standard icon name"
    else
        echo "Desktop file not found in expected location"
    fi
    
    # 5. Create a proper desktop file in the Cinnamon menu location
    echo "Creating desktop file for Cinnamon menu..."
    mkdir -p ~/.local/share/cinnamon/applets/menu@cinnamon.org
    
    CINNAMON_DESKTOP_FILE=~/.local/share/cinnamon/applets/menu@cinnamon.org/com.calendifier.Calendar.desktop
    
    # Create a proper desktop file instead of a symlink
    cat > "$CINNAMON_DESKTOP_FILE" << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Calendifier
GenericName=Calendar Application
Comment=A sophisticated cross-platform desktop calendar application
Icon=com.calendifier.Calendar
Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar
Terminal=false
Categories=Office;Calendar;Qt;
Keywords=calendar;event;schedule;appointment;reminder;date;time;
StartupNotify=true
StartupWMClass=calendifier
X-Cinnamon-UsesNotifications=true
X-GNOME-UsesNotifications=true
EOL
    chmod +x "$CINNAMON_DESKTOP_FILE"
    echo "Created desktop file in Cinnamon menu location."
    
    # 6. Refresh icon cache
    echo "Refreshing icon cache..."
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null || true
    fi
    
    # 7. Create desktop shortcut if Desktop directory exists and no shortcut exists
    if [ -d ~/Desktop ] && [ ! -f ~/Desktop/Calendifier.desktop ]; then
        echo "Creating desktop shortcut..."
        cat > ~/Desktop/Calendifier.desktop << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Calendifier
GenericName=Calendar Application
Comment=A sophisticated cross-platform desktop calendar application
Icon=com.calendifier.Calendar
Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar
Terminal=false
Categories=Office;Calendar;Qt;
Keywords=calendar;event;schedule;appointment;reminder;date;time;
StartupNotify=true
StartupWMClass=calendifier
X-GNOME-UsesNotifications=true
X-Cinnamon-UsesNotifications=true
EOL
        chmod +x ~/Desktop/Calendifier.desktop
        echo "Created desktop shortcut."
    elif [ -f ~/Desktop/Calendifier.desktop ]; then
        echo "Desktop shortcut already exists, updating it..."
        # Update the Exec line to ensure it works
        sed -i "s|^Exec=.*|Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar|g" ~/Desktop/Calendifier.desktop
        chmod +x ~/Desktop/Calendifier.desktop
        echo "Updated desktop shortcut."
    fi
    
    # 8. Try to refresh Cinnamon menu
    echo "Attempting to refresh Cinnamon menu..."
    dbus-send --session --dest=org.Cinnamon --type=method_call /org/Cinnamon org.Cinnamon.Eval string:'Main.panel.menuManager._updateMenus();' &>/dev/null || true
    dbus-send --session --dest=org.Cinnamon --type=method_call /org/Cinnamon org.Cinnamon.Eval string:'Main.placesManager._refreshAll();' &>/dev/null || true
    
    echo "Fedora Cinnamon icon fixes applied successfully!"
    return 0
}

# Function to apply XFCE UI fixes
fix_xfce_ui() {
    echo "===== Applying XFCE UI Fixes ====="
    
    # 1. Create necessary directories
    mkdir -p ~/.config/gtk-3.0
    mkdir -p ~/.config/xfce4/xfconf/xfce-perchannel-xml
    
    # 2. Create a Qt configuration file for XFCE
    mkdir -p ~/.config/qt5ct
    cat > ~/.config/qt5ct/qt5ct.conf << EOL
[Appearance]
icon_theme=elementary-xfce
style=gtk2
EOL

    # 3. Create a Qt6 configuration file for XFCE
    mkdir -p ~/.config/qt6ct
    cat > ~/.config/qt6ct/qt6ct.conf << EOL
[Appearance]
icon_theme=elementary-xfce
style=gtk2
EOL

    # 4. Fix icon paths
    mkdir -p ~/.local/share/icons/hicolor/scalable/apps
    
    # Copy icons to XFCE-specific locations
    if [ -f "$SOURCE_DIR/assets/calendar_icon.svg" ]; then
        cp "$SOURCE_DIR/assets/calendar_icon.svg" ~/.local/share/icons/hicolor/scalable/apps/com.calendifier.Calendar.svg
    fi
    
    # 5. Create desktop file for XFCE using the exact format that works
    echo "Creating desktop file for XFCE..."
    
    # Main desktop file
    DESKTOP_FILE=~/.local/share/applications/com.calendifier.Calendar.desktop
    
    # Create or update main desktop file with the exact format that works
    mkdir -p ~/.local/share/applications
    cat > "$DESKTOP_FILE" << 'EOL'
[Desktop Entry]
Version=1.0
Type=Application
Name=Calendifier
GenericName=Calendar Application
Comment=A sophisticated cross-platform desktop calendar application Icon=com.calendifier.Calendar Terminal=false Categories=Office;Calendar;Qt; Keywords=calendar;event;schedule;appointment;reminder;date;time;
StartupNotify=true
StartupWMClass=calendifier
MimeType=text/calendar;application/ics;
X-Flatpak=com.calendifier.Calendar
Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 com.calendifier.Calendar
EOL
    chmod +x "$DESKTOP_FILE"
    
    # Update desktop database
    update-desktop-database ~/.local/share/applications 2>/dev/null || true
    
    echo "Desktop file created for XFCE."
    
    # 6. Update icon cache
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null || true
    fi
    
    # 7. Refresh XFCE menu cache
    echo "Refreshing XFCE menu cache..."
    if command -v xfce4-panel &> /dev/null; then
        # Try to restart XFCE panel to refresh menu
        xfce4-panel --restart &>/dev/null || true
    fi
    
    # Alternative method to refresh menu cache
    if [ -d ~/.cache/xfce4 ]; then
        echo "Clearing XFCE cache..."
        rm -rf ~/.cache/xfce4/xfce4-applications.menu &>/dev/null || true
    fi
    
    # Update desktop database again to ensure changes are registered
    update-desktop-database ~/.local/share/applications 2>/dev/null || true
    
    # Create a symlink in XFCE-specific locations if they exist
    if [ -d ~/.config/xfce4/panel/launcher-* ]; then
        echo "Creating symlinks in XFCE panel launcher directories..."
        for launcher_dir in ~/.config/xfce4/panel/launcher-*; do
            if [ -d "$launcher_dir" ]; then
                ln -sf ~/.local/share/applications/com.calendifier.Calendar.desktop "$launcher_dir/" 2>/dev/null || true
            fi
        done
    fi
    
    echo "XFCE UI fixes applied successfully!"
    return 0
}

# Function to display installation instructions for flatpak-builder
install_instructions() {
    DISTRO=$(detect_distro)
    echo "flatpak-builder not found. Please install it first."
    
    case $DISTRO in
        "ubuntu" | "debian" | "linuxmint" | "pop")
            echo "On Debian/Ubuntu/Mint/Pop_OS!: sudo apt install flatpak flatpak-builder"
            ;;
        "fedora")
            echo "On Fedora: sudo dnf install flatpak flatpak-builder"
            ;;
        "rhel" | "centos" | "rocky" | "alma")
            echo "On RHEL/CentOS/Rocky/Alma Linux:"
            echo "1. Enable EPEL repository: sudo dnf install epel-release"
            echo "2. Install flatpak: sudo dnf install flatpak flatpak-builder"
            ;;
        "arch" | "manjaro" | "endeavouros")
            echo "On Arch/Manjaro/EndeavourOS: sudo pacman -S flatpak flatpak-builder"
            ;;
        "opensuse" | "opensuse-leap" | "opensuse-tumbleweed")
            echo "On openSUSE: sudo zypper install flatpak flatpak-builder"
            ;;
        "gentoo")
            echo "On Gentoo: sudo emerge --ask dev-util/flatpak dev-util/flatpak-builder"
            ;;
        "void")
            echo "On Void Linux: sudo xbps-install -S flatpak flatpak-builder"
            ;;
        "slackware")
            echo "On Slackware: Use SlackBuilds from https://slackbuilds.org/repository/15.0/development/flatpak/ and https://slackbuilds.org/repository/15.0/development/flatpak-builder/"
            ;;
        *)
            echo "For other distributions, please check your package manager or visit https://flatpak.org/setup/"
            ;;
    esac
    
    echo "After installation, you may need to log out and log back in to update your environment."
    exit 1
}

# Check if flatpak is installed
if ! command -v flatpak &> /dev/null; then
    echo "flatpak not found!"
    install_instructions
fi

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo "flatpak-builder not found!"
    install_instructions
fi

# Check if required files exist
if [ ! -f "main.py" ]; then
    echo "main.py not found. Please run this script from your source directory."
    exit 1
fi

# Verify essential directories exist
if [ ! -d "calendar_app" ]; then
    echo "calendar_app directory not found. Please run this script from your source directory."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found. Creating a minimal requirements file..."
    # Create minimal requirements.txt if missing
    cat > requirements.txt << EOL
PySide6>=6.5.0
ntplib>=0.4.0
python-dateutil>=2.8.0
holidays>=0.34
icalendar>=5.0.0
tzdata>=2025.2
psutil>=5.9.0
EOL
fi

# Detect distribution and desktop environment
DISTRO=$(detect_distro)
DESKTOP=$(detect_desktop)
echo "Detected distribution: $DISTRO"
echo "Detected desktop environment: $DESKTOP"

# Get source directory (where the script is being run from)
SOURCE_DIR="$(pwd)"
echo "Building from source directory: $SOURCE_DIR"

# Create wrapper script for main.py
cat > wrapper.py << 'EOL'
#!/usr/bin/env python3

# Import style initialization first
import style_init
style_init.set_style_for_desktop()

# Then import and run the main application
import main

if __name__ == "__main__":
    main.main()
EOL

# Create runner script to start calendifier directly with enhanced environment detection
cat > calendifier-runner.sh << 'EOL'
#!/bin/bash

# Set Python path to include app directory and site-packages
export PYTHONPATH="/app:/app/lib/python3.12/site-packages:$PYTHONPATH"

# Detect desktop environment
DESKTOP_ENV="unknown"
if [ -n "$XDG_CURRENT_DESKTOP" ]; then
    DESKTOP_ENV="$XDG_CURRENT_DESKTOP"
elif [ -n "$DESKTOP_SESSION" ]; then
    DESKTOP_ENV="$DESKTOP_SESSION"
fi

# Convert to uppercase for easier comparison
DESKTOP_ENV_UPPER=$(echo "$DESKTOP_ENV" | tr '[:lower:]' '[:upper:]')

# PySide6/Qt6 Configuration
export QT_PLUGIN_PATH="/app/lib/python3.12/site-packages/PySide6/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="/app/lib/python3.12/site-packages/PySide6/Qt/plugins/platforms"

# XFCE-specific settings
if [[ "$DESKTOP_ENV_UPPER" == *"XFCE"* ]]; then
    echo 'Calendifier: Detected XFCE environment, applying specific settings'
    export QT_QPA_PLATFORMTHEME=gtk3
    export QT_STYLE_OVERRIDE=gtk2
    export QT_SCALE_FACTOR=1
    # Additional XFCE-specific settings
    export QT_QPA_PLATFORM_PLUGIN=gtk3
    export QT_QPA_PLATFORM_THEME_PATH=/app/lib/python3.12/site-packages/PySide6/Qt/plugins/platformthemes
fi

# Hyprland-specific settings
if [[ "$DESKTOP_ENV_UPPER" == *"HYPRLAND"* ]]; then
    echo 'Calendifier: Detected Hyprland environment, applying specific settings'
    export QT_QPA_PLATFORM=wayland
    export QT_WAYLAND_DISABLE_WINDOWDECORATION=1
    export QT_AUTO_SCREEN_SCALE_FACTOR=1
    export QT_ENABLE_HIGHDPI_SCALING=1
fi

# Platform detection for Wayland/X11
if [ -n "$WAYLAND_DISPLAY" ] && [ -z "$FORCE_X11" ]; then
    export QT_QPA_PLATFORM=wayland
    echo 'Calendifier: Using Wayland platform'
elif [ -n "$DISPLAY" ]; then
    export QT_QPA_PLATFORM=xcb
    echo 'Calendifier: Using X11/XCB platform'
else
    export QT_QPA_PLATFORM=xcb
    echo 'Calendifier: Using XCB as fallback'
fi

# Additional Qt6 environment variables
export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_ENABLE_HIGHDPI_SCALING=1

# Change to app directory and run Calendifier
cd /app
exec python3 wrapper.py "$@"
EOL

# Make runner script executable
chmod +x calendifier-runner.sh

# Create Qt configuration files for better XFCE integration
mkdir -p qt-config
cat > qt-config/qt.conf << 'EOL'
[Paths]
Plugins = plugins
Imports = imports
Qml2Imports = qml
EOL

# Create Qt style configuration
mkdir -p qt-config/qt5
cat > qt-config/qt5/qtbase.conf << 'EOL'
[Appearance]
Style=GTK+
EOL

# Create Qt platform theme configuration
mkdir -p qt-config/qt5/qt5ct
cat > qt-config/qt5/qt5ct/qt5ct.conf << 'EOL'
[Appearance]
custom_palette=false
icon_theme=elementary-xfce
standard_dialogs=default
style=gtk2

[Fonts]
fixed=@Variant(\0\0\0@\0\0\0\x12\0\x44\0\x65\0j\0\x61\0V\0u\0 \0S\0\x61\0n\0s@$\0\0\0\0\0\0\xff\xff\xff\xff\x5\x1\0\x32\x10)
general=@Variant(\0\0\0@\0\0\0\x12\0\x44\0\x65\0j\0\x61\0V\0u\0 \0S\0\x61\0n\0s@$\0\0\0\0\0\0\xff\xff\xff\xff\x5\x1\0\x32\x10)

[Interface]
activate_item_on_single_click=1
buttonbox_layout=0
cursor_flash_time=1000
dialog_buttons_have_icons=1
double_click_interval=400
gui_effects=@Invalid()
keyboard_scheme=2
menus_have_icons=true
show_shortcuts_in_context_menus=true
stylesheets=@Invalid()
toolbutton_style=4
underline_shortcut=1
wheel_scroll_lines=3
EOL

# Create Qt6 configuration
mkdir -p qt-config/qt6/qt6ct
cat > qt-config/qt6/qt6ct/qt6ct.conf << 'EOL'
[Appearance]
custom_palette=false
icon_theme=elementary-xfce
standard_dialogs=default
style=gtk2

[Fonts]
fixed=@Variant(\0\0\0@\0\0\0\x12\0\x44\0\x65\0j\0\x61\0V\0u\0 \0S\0\x61\0n\0s@$\0\0\0\0\0\0\xff\xff\xff\xff\x5\x1\0\x32\x10)
general=@Variant(\0\0\0@\0\0\0\x12\0\x44\0\x65\0j\0\x61\0V\0u\0 \0S\0\x61\0n\0s@$\0\0\0\0\0\0\xff\xff\xff\xff\x5\x1\0\x32\x10)

[Interface]
activate_item_on_single_click=1
buttonbox_layout=0
cursor_flash_time=1000
dialog_buttons_have_icons=1
double_click_interval=400
gui_effects=@Invalid()
keyboard_scheme=2
menus_have_icons=true
show_shortcuts_in_context_menus=true
stylesheets=@Invalid()
toolbutton_style=4
underline_shortcut=1
wheel_scroll_lines=3
EOL

# Create Flatpak manifest with KDE Platform for better Qt6/PySide6 support
python3 -c '
import json

manifest = {
    "app-id": "com.calendifier.Calendar",
    "runtime": "org.kde.Platform",
    "runtime-version": "6.8",
    "sdk": "org.kde.Sdk",
    "command": "calendifier",
    "finish-args": [
        "--share=ipc",
        "--socket=x11",
        "--socket=wayland",
        "--socket=fallback-x11",
        "--device=dri",
        "--share=network",
        "--filesystem=home",
        "--filesystem=xdg-documents",
        "--filesystem=xdg-download",
        "--talk-name=org.freedesktop.Notifications",
        "--talk-name=org.kde.StatusNotifierWatcher",
        "--own-name=com.calendifier.Calendar",
        "--env=QT_QPA_PLATFORMTHEME=gtk3",
        "--env=GDK_BACKEND=x11,wayland",
        "--filesystem=xdg-config/gtk-3.0:ro",
        "--filesystem=xdg-config/gtk-2.0:ro",
        "--filesystem=xdg-config/Trolltech.conf:ro",
        "--filesystem=/usr/share/themes:ro"
    ],
    "build-options": {
        "env": {
            "PIP_CACHE_DIR": "/run/build/calendifier/pip-cache"
        },
        "build-args": [
            "--share=network"
        ]
    },
    "modules": [
        {
            "name": "gtk-integration",
            "buildsystem": "simple",
            "build-commands": [
                "mkdir -p ${FLATPAK_DEST}/lib/gtk-3.0",
                "mkdir -p ${FLATPAK_DEST}/lib/gtk-2.0"
            ]
        },
        {
            "name": "python3-pip",
            "buildsystem": "simple",
            "build-commands": [
                "python3 -m ensurepip --upgrade"
            ]
        },
        {
            "name": "python-dependencies",
            "buildsystem": "simple",
            "build-commands": [
                "pip3 install --no-cache-dir --prefix=${FLATPAK_DEST} PySide6>=6.5.0",
                "python3 -c \"import PySide6; print(\\\"PySide6 version:\\\", PySide6.__version__)\"",
                "pip3 install --no-cache-dir --prefix=${FLATPAK_DEST} ntplib>=0.4.0",
                "pip3 install --no-cache-dir --prefix=${FLATPAK_DEST} python-dateutil>=2.8.0",
                "pip3 install --no-cache-dir --prefix=${FLATPAK_DEST} holidays>=0.34",
                "pip3 install --no-cache-dir --prefix=${FLATPAK_DEST} icalendar>=5.0.0",
                "pip3 install --no-cache-dir --prefix=${FLATPAK_DEST} tzdata>=2025.2",
                "pip3 install --no-cache-dir --prefix=${FLATPAK_DEST} psutil>=5.9.0"
            ]
        },
        {
            "name": "calendifier",
            "buildsystem": "simple",
            "build-commands": [
                "cp -rv main.py ${FLATPAK_DEST}/",
                "cp -rv style_init.py ${FLATPAK_DEST}/",
                "cp -rv wrapper.py ${FLATPAK_DEST}/",
                "chmod +x ${FLATPAK_DEST}/wrapper.py",
                "cp -rv calendar_app ${FLATPAK_DEST}/",
                "if [ -f version.py ]; then cp -rv version.py ${FLATPAK_DEST}/; fi",
                "if [ -d assets ]; then cp -rv assets ${FLATPAK_DEST}/; fi",
                "if [ -f LICENSE ]; then cp -rv LICENSE ${FLATPAK_DEST}/; fi",
                "if [ -f LGPL3_COMPLIANCE_NOTICE.txt ]; then cp -rv LGPL3_COMPLIANCE_NOTICE.txt ${FLATPAK_DEST}/; fi",
                "if [ -f LGPL3_LICENSE.txt ]; then cp -rv LGPL3_LICENSE.txt ${FLATPAK_DEST}/; fi",
                "test -f ${FLATPAK_DEST}/main.py && echo \"main.py successfully copied\" || (echo \"ERROR: main.py not found!\" && exit 1)",
                "test -d ${FLATPAK_DEST}/calendar_app && echo \"calendar_app directory successfully copied\" || (echo \"ERROR: calendar_app directory not found!\" && exit 1)",
                "mkdir -p ${FLATPAK_DEST}/bin",
                "cp calendifier-runner.sh ${FLATPAK_DEST}/bin/calendifier",
                "chmod +x ${FLATPAK_DEST}/bin/calendifier",
                "test -x ${FLATPAK_DEST}/bin/calendifier && echo \"Launcher script created successfully\" || (echo \"ERROR: Launcher script creation failed!\" && exit 1)",
                "install -Dm644 com.calendifier.Calendar.desktop ${FLATPAK_DEST}/share/applications/com.calendifier.Calendar.desktop",
                "install -Dm644 com.calendifier.Calendar.metainfo.xml ${FLATPAK_DEST}/share/metainfo/com.calendifier.Calendar.metainfo.xml",
                "if [ -f assets/calendar_icon.svg ]; then install -Dm644 assets/calendar_icon.svg ${FLATPAK_DEST}/share/icons/hicolor/scalable/apps/com.calendifier.Calendar.svg; fi",
                "if [ -f assets/calendar_icon_256x256.png ]; then install -Dm644 assets/calendar_icon_256x256.png ${FLATPAK_DEST}/share/icons/hicolor/256x256/apps/com.calendifier.Calendar.png; fi",
                "if [ -f assets/calendar_icon_128x128.png ]; then install -Dm644 assets/calendar_icon_128x128.png ${FLATPAK_DEST}/share/icons/hicolor/128x128/apps/com.calendifier.Calendar.png; fi",
                "if [ -f assets/calendar_icon_96x96.png ]; then install -Dm644 assets/calendar_icon_96x96.png ${FLATPAK_DEST}/share/icons/hicolor/96x96/apps/com.calendifier.Calendar.png; fi",
                "if [ -f assets/calendar_icon_64x64.png ]; then install -Dm644 assets/calendar_icon_64x64.png ${FLATPAK_DEST}/share/icons/hicolor/64x64/apps/com.calendifier.Calendar.png; fi",
                "if [ -f assets/calendar_icon_48x48.png ]; then install -Dm644 assets/calendar_icon_48x48.png ${FLATPAK_DEST}/share/icons/hicolor/48x48/apps/com.calendifier.Calendar.png; fi",
                "if [ -f assets/calendar_icon_32x32.png ]; then install -Dm644 assets/calendar_icon_32x32.png ${FLATPAK_DEST}/share/icons/hicolor/32x32/apps/com.calendifier.Calendar.png; fi",
                "if [ -f assets/calendar_icon_24x24.png ]; then install -Dm644 assets/calendar_icon_24x24.png ${FLATPAK_DEST}/share/icons/hicolor/24x24/apps/com.calendifier.Calendar.png; fi",
                "if [ -f assets/calendar_icon_16x16.png ]; then install -Dm644 assets/calendar_icon_16x16.png ${FLATPAK_DEST}/share/icons/hicolor/16x16/apps/com.calendifier.Calendar.png; fi",
                "echo \"Final verification - listing /app contents:\"",
                "ls -la ${FLATPAK_DEST}/",
                "echo \"Testing Python can find main.py:\"",
                "cd ${FLATPAK_DEST} && python3 -c \"import os; print(\\\"main.py exists:\\\", os.path.exists(\\\"main.py\\\"))\"",
            ],
            "sources": [
                {
                    "type": "dir",
                    "path": "."
                }
            ]
        }
    ]
}

# Write the manifest to a file with proper JSON formatting
with open("com.calendifier.Calendar.json", "w") as f:
    json.dump(manifest, f, indent=4)

print("Flatpak manifest created successfully: com.calendifier.Calendar.json")
'

# Create desktop file following Flatpak conventions
cat > com.calendifier.Calendar.desktop << 'EOL'
[Desktop Entry]
Version=1.0
Type=Application
Name=Calendifier
GenericName=Calendar Application
Comment=A sophisticated cross-platform desktop calendar application Icon=com.calendifier.Calendar Terminal=false Categories=Office;Calendar;Qt; Keywords=calendar;event;schedule;appointment;reminder;date;time;
StartupNotify=true
StartupWMClass=calendifier
MimeType=text/calendar;application/ics;
X-Flatpak=com.calendifier.Calendar
Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 com.calendifier.Calendar
EOL

# Add desktop environment specific entries
case "$DESKTOP" in
    *"Cinnamon"* | *"CINNAMON"* | *"X-Cinnamon"*)
        echo "Adding Cinnamon-specific desktop entries..."
        cat >> com.calendifier.Calendar.desktop << 'EOL'
X-Cinnamon-UsesNotifications=true
X-GNOME-UsesNotifications=true
EOL
        ;;
    *"GNOME"* | *"UBUNTU"*)
        echo "Adding GNOME-specific desktop entries..."
        cat >> com.calendifier.Calendar.desktop << 'EOL'
X-GNOME-UsesNotifications=true
EOL
        ;;
    *"KDE"* | *"PLASMA"*)
        echo "Adding KDE-specific desktop entries..."
        cat >> com.calendifier.Calendar.desktop << 'EOL'
X-KDE-FormFactor=desktop,tablet,handset
X-KDE-StartupNotify=true
EOL
        ;;
    *"XFCE"* | *"Xfce"*)
        echo "Adding XFCE-specific desktop entries..."
        cat >> com.calendifier.Calendar.desktop << 'EOL'
X-XFCE-Source=file:///usr/share/applications/com.calendifier.Calendar.desktop
Exec=flatpak run com.calendifier.Calendar
EOL
        ;;
    *"Hyprland"* | *"HYPRLAND"*)
        echo "Adding Hyprland-specific desktop entries..."
        cat >> com.calendifier.Calendar.desktop << 'EOL'
X-GNOME-UsesNotifications=true
Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --env=QT_QPA_PLATFORM=wayland --env=QT_WAYLAND_DISABLE_WINDOWDECORATION=1 --command=calendifier com.calendifier.Calendar
EOL
        ;;
    *)
        # Default entries for other desktop environments
        cat >> com.calendifier.Calendar.desktop << 'EOL'
X-GNOME-UsesNotifications=true
EOL
        ;;
esac

# Extract version from version.py
APP_VERSION=""
if [ -f "version.py" ]; then
    # Extract version with more robust error handling
    APP_VERSION=$(python3 -c "exec(open('version.py').read()); print(__version__)" 2>/dev/null)
    
    # Check if extraction was successful
    if [ -z "$APP_VERSION" ]; then
        APP_VERSION="1.1.0"
    fi
else
    APP_VERSION="1.1.0"
fi

echo "Using version: $APP_VERSION"

# Create metainfo file
cat > com.calendifier.Calendar.metainfo.xml << EOL
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.calendifier.Calendar</id>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <name>Calendifier</name>
  <summary>A sophisticated cross-platform desktop calendar application</summary>
  <description>
    <p>
      Calendifier is a feature-rich, cross-platform desktop calendar built with Python and PySide6,
      designed to serve users worldwide with native-quality localization and intelligent holiday management.
    </p>
    <p>Features:</p>
    <ul>
      <li>Full Calendar Management with monthly view and intuitive navigation</li>
      <li>14-Language Support with complete localization and runtime language switching</li>
      <li>14-Country Holiday Support with intelligent holiday detection and native translations</li>
      <li>Real-time Analog Clock with NTP synchronization for accurate timekeeping</li>
      <li>Comprehensive Event Management with categories and recurring events</li>
      <li>Dynamic Theming with Dark/Light mode and instant switching</li>
      <li>Integrated Notes with built-in note-taking functionality</li>
      <li>Import/Export support for iCalendar, CSV, and JSON formats</li>
      <li>Extensive Configuration with customizable settings for all preferences</li>
    </ul>
  </description>
  <launchable type="desktop-id">com.calendifier.Calendar.desktop</launchable>
  <provides>
    <binary>calendifier</binary>
  </provides>
  <url type="homepage">https://github.com/oernster/calendifier</url>
  <url type="bugtracker">https://github.com/oernster/calendifier/issues</url>
  <url type="help">https://github.com/oernster/calendifier/blob/main/README.md</url>
  <developer_name>Oliver Ernster</developer_name>
  <update_contact>oliver.ernster@example.com</update_contact>
  <releases>
    <release version="$APP_VERSION" date="2025-06-28">
      <description>
        <p>Version $APP_VERSION with improved layout and user interface enhancements.</p>
      </description>
    </release>
  </releases>
  <content_rating type="oars-1.1"/>
  <supports>
    <control>pointing</control>
    <control>keyboard</control>
  </supports>
  <categories>
    <category>Office</category>
    <category>Calendar</category>
    <category>Qt</category>
  </categories>
</component>
EOL

# Function to setup Flathub repository
setup_flathub() {
    # Remove existing Flathub remote if it exists and is causing issues
    echo "Removing existing Flathub remote if it exists..."
    flatpak remote-delete --force flathub 2>/dev/null || true

    # Add Flathub repository with the correct URL based on distribution
    echo "Adding Flathub repository with correct URL..."
    if [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" || "$DISTRO" == "endeavouros" ]]; then
        flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    else
        flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    fi

    # Verify the remote is correctly added
    echo "Verifying Flathub remote configuration..."
    flatpak remotes
}

# Setup Flathub repository
setup_flathub

# Install required KDE 6.8 runtimes with specific distribution handling
echo "Installing KDE 6.8 Platform and SDK (optimized for Qt6/PySide6)..."

# Check for Arch-based systems with special handling
if [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" || "$DISTRO" == "endeavouros" ]]; then
    echo "Detected Arch-based system. Using special installation procedure..."
    
    # First try to install the runtime with user installation
    if ! flatpak install --user -y flathub org.kde.Platform//6.8; then
        echo "User installation failed. Trying system installation..."
        if ! sudo flatpak install -y flathub org.kde.Platform//6.8; then
            echo "Failed to install KDE Platform runtime. Please check your internet connection."
            echo "You may need to install the ca-certificates package: sudo pacman -S ca-certificates"
            echo "Also ensure your Flathub repository is correctly configured."
            exit 1
        fi
    fi
    
    # Then install the SDK
    if ! flatpak install --user -y flathub org.kde.Sdk//6.8; then
        echo "User installation failed. Trying system installation..."
        if ! sudo flatpak install -y flathub org.kde.Sdk//6.8; then
            echo "Failed to install KDE SDK runtime. Please check your internet connection."
            exit 1
        fi
    fi
else
    # For non-Arch systems, use the original method
    if ! flatpak install --user -y flathub org.kde.Platform//6.8; then
        echo "Failed to install KDE Platform runtime. Please check your internet connection."
        case $DISTRO in
            "ubuntu" | "debian" | "linuxmint" | "pop")
                echo "You may need to install the ca-certificates package: sudo apt install ca-certificates"
                ;;
            "fedora" | "rhel" | "centos" | "rocky" | "alma")
                echo "You may need to install the ca-certificates package: sudo dnf install ca-certificates"
                ;;
        esac
        exit 1
    fi

    if ! flatpak install --user -y flathub org.kde.Sdk//6.8; then
        echo "Failed to install KDE SDK runtime. Please check your internet connection."
        exit 1
    fi
fi

echo "Building Flatpak..."

# Create build directory if it doesn't exist
mkdir -p build

# Clean any previous builds
rm -rf build/* 2>/dev/null || true

# Create special permissions for Arch/EndeavourOS with Cinnamon
if [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" || "$DISTRO" == "endeavouros" ]]; then
    echo "Configuring special permissions for Arch-based systems..."
    
    # Create temporary file with fixed permissions for Cinnamon
    cat > flatpak_override_settings << EOL
[Context]
shared=network;ipc;
sockets=x11;wayland;
devices=dri;
filesystems=xdg-documents:ro;xdg-download:ro;
EOL
    
    echo "Will apply these custom permissions after build."
fi

# Build the Flatpak with dependencies from Flathub
echo "Building with flatpak-builder..."
if ! flatpak-builder --verbose --user --install-deps-from=flathub --force-clean build com.calendifier.Calendar.json; then
    echo "Flatpak build failed. Trying with alternative build options..."
    
    # Attempt with different options for Arch
    if [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" || "$DISTRO" == "endeavouros" ]]; then
        echo "Trying alternate build for Arch systems..."
        if ! flatpak-builder --verbose --user --install-deps-from=flathub --force-clean --keep-build-dirs build com.calendifier.Calendar.json; then
            echo "Alternative build also failed. This could be due to network issues or missing dependencies."
            echo "Check the build logs in the build directory for more details."
            exit 1
        fi
    else
        echo "Flatpak build failed. This could be due to network issues or missing dependencies."
        echo "If you're behind a proxy, make sure to set the http_proxy and https_proxy environment variables."
        exit 1
    fi
fi

echo "Creating repository..."
flatpak-builder --repo=repo --force-clean --user build com.calendifier.Calendar.json

echo "Creating single-file bundle..."

# Get repository size for estimation
REPO_SIZE_BYTES=$(du -sb repo 2>/dev/null | cut -f1 || echo "0")
REPO_SIZE_MB=$(( REPO_SIZE_BYTES / 1048576 ))
echo "Repository size: ${REPO_SIZE_MB} MB"

echo "Running: flatpak build-bundle repo calendifier.flatpak com.calendifier.Calendar"
echo ""

# Start bundle creation with verbose output
flatpak build-bundle --verbose repo calendifier.flatpak com.calendifier.Calendar > /tmp/flatpak-bundle.log 2>&1 &
BUNDLE_PID=$!

# Monitor progress
last_milestone=""
last_size=0
no_progress_count=0

while kill -0 $BUNDLE_PID 2>/dev/null; do
    # Check for milestones in the log
    if [ -f /tmp/flatpak-bundle.log ]; then
        # Look for key progress indicators with case-insensitive matching
        if grep -qi "export" /tmp/flatpak-bundle.log && [ "$last_milestone" != "exporting" ]; then
            echo ""
            echo "[1/4] Exporting files..."
            last_milestone="exporting"
        elif grep -qi "writ" /tmp/flatpak-bundle.log && [ "$last_milestone" != "writing" ]; then
            echo ""
            echo "[2/4] Writing bundle data..."
            last_milestone="writing"
        elif grep -qi "commit" /tmp/flatpak-bundle.log && [ "$last_milestone" != "committing" ]; then
            echo ""
            echo "[3/4] Committing changes..."
            last_milestone="committing"
        elif grep -qi "compress\|pack" /tmp/flatpak-bundle.log && [ "$last_milestone" != "compressing" ]; then
            echo ""
            echo "[4/4] Compressing bundle..."
            last_milestone="compressing"
        fi
    fi
    
    # Monitor bundle file size
    if [ -f "calendifier.flatpak" ]; then
        current_size=$(stat -c%s "calendifier.flatpak" 2>/dev/null || echo "0")
        if [ "$current_size" -gt "$last_size" ]; then
            size_mb=$(( current_size / 1048576 ))
            if [ $REPO_SIZE_BYTES -gt 0 ]; then
                percent=$(( current_size * 100 / REPO_SIZE_BYTES ))
                printf "\r📦 Bundle progress: %d MB (%d%% of repository size)" "$size_mb" "$percent"
            else
                printf "\r📦 Bundle progress: %d MB" "$size_mb"
            fi
            last_size=$current_size
            no_progress_count=0
        else
            no_progress_count=$((no_progress_count + 1))
            if [ $no_progress_count -gt 20 ]; then
                echo ""
                echo "⏳ Finalizing bundle..."
                break
            fi
        fi
    fi
    
    sleep 0.5
done

# Wait for completion
wait $BUNDLE_PID
BUNDLE_EXIT_CODE=$?

echo ""  # New line after progress

# Check result
if [ $BUNDLE_EXIT_CODE -eq 0 ] && [ -f "calendifier.flatpak" ]; then
    echo "✅ Bundle creation completed successfully!"
    BUNDLE_SIZE=$(du -h calendifier.flatpak | cut -f1)
    echo "📦 Final bundle size: $BUNDLE_SIZE"
    
    # If no milestones were shown, display what was in the log
    if [ "$last_milestone" = "" ] && [ -f /tmp/flatpak-bundle.log ]; then
        echo ""
        echo "Note: Progress milestones were not detected. Log tail:"
        tail -n 5 /tmp/flatpak-bundle.log
    fi
else
    echo "❌ Bundle creation failed"
    echo "You can still install from the repo with: flatpak install --user repo com.calendifier.Calendar"
    echo "Or try creating the bundle manually with: flatpak build-bundle repo calendifier.flatpak com.calendifier.Calendar"
    
    # Show error details from log
    if [ -f /tmp/flatpak-bundle.log ]; then
        echo ""
        echo "Error details from log:"
        tail -n 10 /tmp/flatpak-bundle.log
    fi
    # Don't exit - the repo is still valid
fi

echo "Done! You can install the Flatpak with:"
echo "flatpak install --user calendifier.flatpak"

# Ask if user wants to install the Flatpak
read -p "Do you want to install the Flatpak now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing Flatpak..."
    flatpak install --user -y calendifier.flatpak
    
    # Check if installation was successful
    if flatpak list | grep -q com.calendifier.Calendar; then
        echo "Flatpak installed successfully."
        
        # Apply custom overrides for Arch/EndeavourOS if needed
        if [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" || "$DISTRO" == "endeavouros" ]]; then
            echo "Applying custom permission overrides for better compatibility with $DISTRO..."
            mkdir -p ~/.local/share/flatpak/overrides
            cp flatpak_override_settings ~/.local/share/flatpak/overrides/com.calendifier.Calendar
            echo "Custom permissions applied."
        fi
        
        # Apply custom overrides for Fedora+Cinnamon
        if [[ "$DISTRO" == "fedora" && ("$DESKTOP" == *"Cinnamon"* || "$DESKTOP" == *"CINNAMON"* || "$DESKTOP" == *"X-Cinnamon"*) ]]; then
            echo "Applying Fedora+Cinnamon specific overrides..."
            mkdir -p ~/.local/share/flatpak/overrides
            cat > ~/.local/share/flatpak/overrides/com.calendifier.Calendar << EOL
[Context]
shared=network;ipc;
sockets=x11;wayland;
devices=dri;
filesystems=xdg-documents:ro;xdg-download:ro;~/.config/cinnamon:ro;~/.local/share/cinnamon:ro;
EOL
            echo "Fedora+Cinnamon overrides applied."
        fi
        
        # Apply custom overrides for XFCE
        if [[ "$DESKTOP" == *"XFCE"* || "$DESKTOP" == *"Xfce"* ]]; then
            echo "Applying XFCE-specific overrides..."
            fix_xfce_ui
            
            echo "XFCE setup completed."
        fi
        
        # Apply custom overrides for Hyprland
        if [[ "$DESKTOP" == *"Hyprland"* || "$DESKTOP" == *"HYPRLAND"* ]]; then
            echo "Applying Hyprland-specific overrides..."
            mkdir -p ~/.local/share/flatpak/overrides
            cat > ~/.local/share/flatpak/overrides/com.calendifier.Calendar << EOL
[Context]
shared=network;ipc;
sockets=wayland;x11;
devices=dri;
filesystems=xdg-documents:ro;xdg-download:ro;
[Environment]
QT_QPA_PLATFORM=wayland
QT_WAYLAND_DISABLE_WINDOWDECORATION=1
QT_AUTO_SCREEN_SCALE_FACTOR=1
QT_ENABLE_HIGHDPI_SCALING=1
EOL
            echo "Hyprland overrides applied."
        fi
        
        echo "You can run it with: flatpak run com.calendifier.Calendar"
        
        # Enhanced desktop integration
        echo "Setting up desktop integration..."
        
        # Get the location of the exported desktop file
        EXPORTED_DESKTOP_FILE=$(find ~/.local/share/flatpak/exports/share/applications -name "com.calendifier.Calendar.desktop" 2>/dev/null)
        
        if [ -n "$EXPORTED_DESKTOP_FILE" ]; then
            mkdir -p ~/.local/share/applications
            cp "$EXPORTED_DESKTOP_FILE" ~/.local/share/applications/com.calendifier.Calendar.desktop
            DESKTOP_FILE=~/.local/share/applications/com.calendifier.Calendar.desktop
            
            # Ensure the Exec line is correct for all desktop environments
            case "$DESKTOP" in
                *"GNOME"* | *"UBUNTU"*)
                    echo "Updating desktop file for GNOME..."
                    sed -i "s|^Exec=.*|Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar|g" "$DESKTOP_FILE"
                    ;;
                *"KDE"* | *"PLASMA"*)
                    echo "Updating desktop file for KDE..."
                    sed -i "s|^Exec=.*|Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar|g" "$DESKTOP_FILE"
                    ;;
                *"Hyprland"* | *"HYPRLAND"*)
                    echo "Updating desktop file for Hyprland..."
                    sed -i "s|^Exec=.*|Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --env=QT_QPA_PLATFORM=wayland --env=QT_WAYLAND_DISABLE_WINDOWDECORATION=1 --command=calendifier com.calendifier.Calendar|g" "$DESKTOP_FILE"
                    ;;
            esac
            
            # Ensure proper permissions
            chmod +x "$DESKTOP_FILE"
            
            # Update the desktop database
            update-desktop-database ~/.local/share/applications 2>/dev/null || true
            
            echo "Desktop file updated successfully."
            
            # Copy icon to standard locations
            mkdir -p ~/.local/share/icons/hicolor/128x128/apps/
            
            # Try to extract icon from flatpak
            if [ -f "$SOURCE_DIR/assets/calendar_icon_128x128.png" ]; then
                cp "$SOURCE_DIR/assets/calendar_icon_128x128.png" ~/.local/share/icons/hicolor/128x128/apps/com.calendifier.Calendar.png
            elif [ -f "$SOURCE_DIR/assets/calendar_icon.png" ]; then
                cp "$SOURCE_DIR/assets/calendar_icon.png" ~/.local/share/icons/hicolor/128x128/apps/com.calendifier.Calendar.png
            fi
            
            if command -v gtk-update-icon-cache &> /dev/null; then
                gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null || true
            fi
            
            # Verify the desktop file
            echo "Verifying desktop file content:"
            cat "$DESKTOP_FILE"
        else
            echo "No exported desktop file found. Creating a new one..."
            DESKTOP_FILE=~/.local/share/applications/com.calendifier.Calendar.desktop
            mkdir -p ~/.local/share/applications
            
            # Create a basic desktop file
            cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Calendifier
GenericName=Calendar Application
Comment=A sophisticated cross-platform desktop calendar application
Icon=com.calendifier.Calendar
EOL
            
            # Add desktop-specific Exec line
            case "$DESKTOP" in
                *"XFCE"* | *"Xfce"*)
                    echo "Exec=flatpak run com.calendifier.Calendar" >> "$DESKTOP_FILE"
                    echo "X-XFCE-Source=file:///usr/share/applications/com.calendifier.Calendar.desktop" >> "$DESKTOP_FILE"
                    ;;
                *"GNOME"* | *"UBUNTU"*)
                    echo "Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar" >> "$DESKTOP_FILE"
                    echo "X-GNOME-UsesNotifications=true" >> "$DESKTOP_FILE"
                    ;;
                *"KDE"* | *"PLASMA"*)
                    echo "Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar" >> "$DESKTOP_FILE"
                    echo "X-KDE-FormFactor=desktop,tablet,handset" >> "$DESKTOP_FILE"
                    echo "X-KDE-StartupNotify=true" >> "$DESKTOP_FILE"
                    ;;
                *"Hyprland"* | *"HYPRLAND"*)
                    echo "Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --env=QT_QPA_PLATFORM=wayland --env=QT_WAYLAND_DISABLE_WINDOWDECORATION=1 --command=calendifier com.calendifier.Calendar" >> "$DESKTOP_FILE"
                    echo "X-GNOME-UsesNotifications=true" >> "$DESKTOP_FILE"
                    ;;
                *"Cinnamon"* | *"CINNAMON"* | *"X-Cinnamon"*)
                    echo "Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar" >> "$DESKTOP_FILE"
                    echo "X-Cinnamon-UsesNotifications=true" >> "$DESKTOP_FILE"
                    echo "X-GNOME-UsesNotifications=true" >> "$DESKTOP_FILE"
                    ;;
                *)
                    echo "Exec=/usr/bin/flatpak run --branch=master --arch=x86_64 --command=calendifier com.calendifier.Calendar" >> "$DESKTOP_FILE"
                    echo "X-GNOME-UsesNotifications=true" >> "$DESKTOP_FILE"
                    ;;
            esac
            
            # Add common entries
            cat >> "$DESKTOP_FILE" << EOL
Terminal=false
Categories=Office;Calendar;Qt;
Keywords=calendar;event;schedule;appointment;reminder;date;time;
StartupNotify=true
StartupWMClass=calendifier
MimeType=text/calendar;application/ics;
X-Flatpak=com.calendifier.Calendar
EOL
            
            # Ensure proper permissions
            chmod +x "$DESKTOP_FILE"
            
            # Update the desktop database
            update-desktop-database ~/.local/share/applications 2>/dev/null || true
            
            echo "Created new desktop file."
        fi
        
        # Apply enhanced icon fixes for Fedora+Cinnamon
        if [[ "$DISTRO" == "fedora" && ("$DESKTOP" == *"Cinnamon"* || "$DESKTOP" == *"CINNAMON"* || "$DESKTOP" == *"X-Cinnamon"*) ]]; then
            echo "Applying enhanced icon fixes for Fedora+Cinnamon..."
            fix_fedora_cinnamon_icon
        fi
        
        # Special menu integration for Cinnamon
        if [[ "$DESKTOP" == *"Cinnamon"* || "$DESKTOP" == *"CINNAMON"* || "$DESKTOP" == *"X-Cinnamon"* ]]; then
            echo "Applying special Cinnamon menu integration..."
            
            # Force refresh Cinnamon menu
            if pgrep -x "cinnamon" > /dev/null; then
                echo "Refreshing Cinnamon menu..."
                
                # Try to refresh Cinnamon via DBus
                dbus-send --session --dest=org.Cinnamon --type=method_call /org/Cinnamon org.Cinnamon.Eval string:'Main.panel.menuManager._updateMenus();' &> /dev/null || true
            fi
            
            echo "Menu integration completed. You may need to log out and back in for the menu entry to appear."
        fi
        
        # Test the installation
        echo ""
        echo "🧪 Testing the installation..."
        echo "Running: flatpak run com.calendifier.Calendar --version"
        timeout 10s flatpak run com.calendifier.Calendar --version 2>/dev/null || echo "Version check completed (or timed out)"
        
    else
        echo "Installation failed. Please try installing manually with: flatpak install --user calendifier.flatpak"
    fi
fi

# Print information about distributing the Flatpak
echo ""
echo "================================================================"
echo "DISTRIBUTION INFORMATION"
echo "================================================================"
echo "The generated Flatpak package 'calendifier.flatpak' can now be distributed"
echo "to other users and systems. Users can install it with:"
echo ""
echo "flatpak install calendifier.flatpak"
echo ""
echo "The Flatpak is self-contained and works on any Linux distribution"
echo "that supports Flatpak, regardless of the user's home directory or username."
echo "The necessary KDE runtime will be automatically downloaded if needed."
echo ""
echo "Runtime used: org.kde.Platform//6.8 (includes complete Qt6 support for PySide6)"
echo "================================================================"