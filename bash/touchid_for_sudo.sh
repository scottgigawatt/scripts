#!/bin/bash

# Retrieve current user information
CURRENT_USER=$(stat -f %Su /dev/console)
USER_ID=$(id -u "$CURRENT_USER")

# Function to configure Sudo Touch ID for macOS 14 and above
configure_touch_id_macos14() {
    local sudo_local_path="/private/etc/pam.d/sudo_local"
    local third_line=$(sed -n 3p "$sudo_local_path" 2>/dev/null)

    if [[ "$third_line" == "auth       sufficient     pam_tid.so" ]]; then
        osascript -e 'tell application (path to frontmost application as text) to display dialog "Sudo Touch ID is already configured." buttons {"OK"} with icon note'
    else
        cp "$sudo_local_path.template" "$sudo_local_path"
        sed -i '.bak' '3s/#//' "$sudo_local_path"
        osascript -e 'tell application (path to frontmost application as text) to display dialog "Sudo Touch ID is now enabled.\nPlease restart your Terminal." buttons {"OK"} with icon note'
    fi
}

# Function to configure Sudo Touch ID for macOS 13 and below
configure_touch_id_macos13() {
    local sudo_path="/private/etc/pam.d/sudo"
    local second_line=$(sed -n 2p "$sudo_path" 2>/dev/null)

    if [[ "$second_line" == "auth       sufficient     pam_tid.so" ]]; then
        osascript -e 'tell application (path to frontmost application as text) to display dialog "Sudo Touch ID is already configured." buttons {"OK"} with icon note'
    else
        sed -i '.bak' '2s/^/auth       sufficient     pam_tid.so\'$'\n/' "$sudo_path"
        osascript -e 'tell application (path to frontmost application as text) to display dialog "Sudo Touch ID is now enabled.\nPlease restart your Terminal." buttons {"OK"} with icon note'
    fi
}

# Detect macOS version and apply configuration
macos_version=$(sw_vers -productVersion | cut -d. -f1)

if [[ "$macos_version" -ge 14 ]]; then
    echo "macOS version is 14 or above. Configuring Sudo Touch ID."
    configure_touch_id_macos14
else
    echo "macOS version is 13 or below. Configuring Sudo Touch ID."
    configure_touch_id_macos13
fi

# Adjust iTerm2 settings to disable session persistence
iterm2_preferences="/Users/$CURRENT_USER/Library/Preferences/com.googlecode.iterm2.plist"
if [[ -e "$iterm2_preferences" ]]; then
    echo "Updating iTerm2 settings to disable session persistence."
    launchctl asuser "$USER_ID" sudo -u "$CURRENT_USER" defaults write com.googlecode.iterm2 BootstrapDaemon -bool false
fi

exit 0
