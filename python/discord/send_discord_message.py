#
# send_discord_message.py
#
# A Python script to send messages to a Discord channel using a webhook.
#
# This script reads configuration details from a YAML file (config.yml) and sends
# a message to a specified Discord channel via a webhook. The message includes:
# - A user mention (tag) using their Discord user ID.
# - An embed with a title, description, and color.
#
# Requirements:
# - Python 3.x
# - requests (for making HTTP requests)
# - PyYAML (for reading the YAML configuration file)
#
# Usage:
# 1. Create a 'config.yml' file in the same directory with all necessary fields.
# 2. Run the script using: python send_discord_message.py
#
# Ensure you have your 'config.yml' properly set up with all required fields:
# - webhook_url: The Discord webhook URL to post messages to.
# - user_to_tag: The Discord user ID to tag in the message.
# - hex_color: The color of the embed in hexadecimal format.
# - title: The title of the embed.
# - message: The content of the message to be sent.
#

import requests  # Library for making HTTP requests
import json      # Library for handling JSON data
import yaml      # Library for reading YAML files


def send_discord_message(webhook_url, user_to_tag, title, message, color):
    """
    Sends a message to a Discord channel using a webhook.

    Args:
        webhook_url (str): The Discord webhook URL.
        user_to_tag (str): The Discord user ID to tag in the message.
        title (str): The title of the embed message.
        message (str): The content of the embed message.
        color (int): The color of the embed in decimal format.
    """

    # Create the content to tag the user
    content = f"<@{user_to_tag}>"

    # Define the embed structure
    embed = {
        "title": title,
        "description": message,
        "color": color  # Color should be in decimal format
    }

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
    title = config.get("title")
    message = config.get("message")

    # Validate that all required fields are present
    if not webhook_url or not user_to_tag or not hex_color or not title or not message:
        print("Error: Missing required information in config.yml.")
        exit(1)

    # Convert the hex color to decimal format required by Discord
    try:
        color = int(hex_color, 16)
    except ValueError:
        print("Error: Invalid hex color format in config.yml.")
        exit(1)

    # Send the message to Discord
    send_discord_message(webhook_url, user_to_tag, title, message, color)
