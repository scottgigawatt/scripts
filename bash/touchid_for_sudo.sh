#!/usr/bin/env bash

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# touchid_for_sudo.sh: Enable macOS Touch ID for sudo and adjust iTerm2 session persistence.
#

# Retrieve current user information
CURRENT_USER=$(stat -f %Su /dev/console)
USER_ID=$(id -u "$CURRENT_USER")

#
# configure_touch_id_macos14: Configure Touch ID through the macOS 14 or newer PAM override.
#
# Parameters: None.
#
# Returns: Status of the dialog or final configuration command.
#
configure_touch_id_macos14() {
    local sudo_local_path="/private/etc/pam.d/sudo_local"
    local third_line
    third_line=$(sed -n 3p "$sudo_local_path" 2>/dev/null)

    if [[ "$third_line" == "auth       sufficient     pam_tid.so" ]]; then
        osascript -e 'tell application (path to frontmost application as text) to display dialog "Sudo Touch ID is already configured." buttons {"OK"} with icon note'
    else
        cp "$sudo_local_path.template" "$sudo_local_path"
        sed -i '.bak' '3s/#//' "$sudo_local_path"
        osascript -e 'tell application (path to frontmost application as text) to display dialog "Sudo Touch ID is now enabled.\nPlease restart your Terminal." buttons {"OK"} with icon note'
    fi
}

#
# configure_touch_id_macos13: Configure Touch ID through the macOS 13 or older PAM sudo file.
#
# Parameters: None.
#
# Returns: Status of the dialog or final configuration command.
#
configure_touch_id_macos13() {
    local sudo_path="/private/etc/pam.d/sudo"
    local second_line
    second_line=$(sed -n 2p "$sudo_path" 2>/dev/null)

    if [[ "$second_line" == "auth       sufficient     pam_tid.so" ]]; then
        osascript -e 'tell application (path to frontmost application as text) to display dialog "Sudo Touch ID is already configured." buttons {"OK"} with icon note'
    else
        # BSD sed needs a backslash followed by a literal newline in this replacement.
        sed -i '.bak' $'2s/^/auth       sufficient     pam_tid.so\\\n/' "$sudo_path"
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
