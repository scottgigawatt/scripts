# -----------------------------------------------------------------------------
# send_discord_message.py
#
# A Python script to send customized messages to a Discord channel using a webhook.
# Reads settings from a YAML config file specified via the command line.
#
# Usage:
#   python send_discord_message.py <config.yml>
#
# Requirements:
# - Python 3.x
# - requests, PyYAML
# -----------------------------------------------------------------------------

import requests  # Library for making HTTP requests
import json      # Library for handling JSON data
import yaml      # Library for reading YAML files
import sys       # Library for handling command-line arguments
from datetime import datetime  # Library for handling date and time
from datetime import timezone

def send_discord_message(webhook_url, user_to_tag, header, title, message, color, fields, thumbnail_url):
    """
    Sends a message to a Discord channel using a webhook.

    Args:
        webhook_url (str): The Discord webhook URL.
        user_to_tag (str): The Discord user ID to tag in the message.
        header (str): The header text of the embed.
        title (str): The title of the embed message.
        message (str): The content of the embed message.
        color (int): The color of the embed in decimal format.
        fields (list of dict): A list of fields to add to the embed.
        thumbnail_url (str): The URL of the thumbnail image for the embed.
    """

    # Create the content to tag the user
    content = f"<@{user_to_tag}>"

    # Get the current Unix timestamp
    current_timestamp = int(datetime.now().timestamp())

    # Define the embed structure
    embed = {
        "author": {  # Add a header/author to the embed
            "name": header
        },
        "title": title,
        "description": message,
        "color": color,  # Color should be in decimal format
        "timestamp": datetime.fromtimestamp(current_timestamp, tz=timezone.utc).isoformat(),
        "footer": {
            "text": "Timestamp"
        },
        "fields": fields if fields else []  # Add fields if specified
    }

    # Add the thumbnail URL to the embed if it is specified
    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}

    # Prepare the data payload to send to the webhook
    data = {
        "content": content,
        "embeds": [embed]
    }

    # Send the request to the Discord webhook
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))

    # Check the response status and print appropriate messages
    if response.status_code == 204:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")


if __name__ == "__main__":
    # Check if the config file was provided as a command line argument
    if len(sys.argv) < 2:
        print("Usage: python send_discord_message.py <config.yml>")
        exit(1)

    config_file = sys.argv[1]

    # Read configuration from the YAML file
    try:
        with open(config_file, "r") as ymlfile:
            config = yaml.safe_load(ymlfile)  # Load the YAML configuration file
    except FileNotFoundError:
        print(f"Error: {config_file} not found in the current directory.")
        exit(1)

    # Extract data from the YAML configuration
    webhook_url = config.get("webhook_url")
    user_to_tag = config.get("user_to_tag")
    hex_color = config.get("hex_color")
    header = config.get("header")
    title = config.get("title")
    message = config.get("message")
    fields = config.get("fields", [])
    thumbnail_url = config.get("thumbnail_url")

    # Validate that all required fields are present
    if not webhook_url or not user_to_tag or not hex_color or not header or not title or not message:
        print("Error: Missing required information in config.yml.")
        exit(1)

    # Convert the hex color to decimal format required by Discord
    try:
        color = int(hex_color, 16)
    except ValueError:
        print("Error: Invalid hex color format in config.yml.")
        exit(1)

    # Send the message to Discord
    send_discord_message(webhook_url, user_to_tag, header, title, message, color, fields, thumbnail_url)
