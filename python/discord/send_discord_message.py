# -----------------------------------------------------------------------------
# send_discord_message.py
#
# A Python script to send customizable messages to a Discord channel using a webhook.
# Reads configuration from 'config.yml' and constructs an embed with options like:
# - Tagging a user, custom title, description, and color.
# - Optional fields, header, thumbnail, and timestamp.
#
# Requirements:
# - Python 3.x
# - requests, PyYAML
#
# Usage:
# 1. Configure 'config.yml' with necessary details (webhook URL, user ID, etc.).
# 2. Run: python send_discord_message.py
# -----------------------------------------------------------------------------

import requests  # Library for making HTTP requests
import json      # Library for handling JSON data
import yaml      # Library for reading YAML files
from datetime import datetime  # Library for handling date and time


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

    # Get the current timestamp in the desired format with AM/PM
    current_time = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    # Define the embed structure
    embed = {
        "author": {  # Add a header/author to the embed
            "name": header
        },
        "title": title,
        "description": message,
        "color": color,  # Color should be in decimal format
        "footer": {  # Add a footer with the timestamp
            "text": f"{current_time}"
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
    # Read configuration from the YAML file
    try:
        with open("config.yml", "r") as ymlfile:
            config = yaml.safe_load(ymlfile)  # Load the YAML configuration file
    except FileNotFoundError:
        print("Error: config.yml not found in the current directory.")
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
