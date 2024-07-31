# Telegram-Bulk-File-Uploader-Bot
A Python-based Telegram bot designed to efficiently upload and manage bulk files to a specified group or channel. The bot supports both image and document files, ensures retries on failures, and tracks upload statuses using a SQLite database.

## Overview
This repository contains a Python-based Telegram bot that automates the process of uploading bulk files (images and documents) to a specified Telegram group or channel. The bot is designed to handle retries on failures and track the status of uploads using a SQLite database.

## Features
- Bulk upload of images and documents to Telegram groups or channels.
- Retry mechanism for failed uploads.
- SQLite database for tracking upload statuses.
- Configurable batch size for media uploads.

## Getting Started

### Prerequisites
- Python 3.8+
- Telegram Bot Token (You can create a bot and get the token from BotFather)

### Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/telegram-bulk-file-uploader.git
    cd telegram-bulk-file-uploader
    ```

2. **Install required packages:**

3. **Configure the bot:**
    - Replace `TOKEN` with your bot token from BotFather.
    - Update `root_directory` with the path to your files.
    - Update `chat_id_file_directory` with your group chat IDs and directories.

4. **Run the bot:**
    ```bash
    python telegram-bulk-file-uploader.py
    ```

## Usage
- Ensure the bot is invited to the group and promoted to an admin.
- Place the files in the specified directories.
- Run the bot script to start uploading.

## File Structure
- `telegram-bulk-file-uploader.py`: Main script for running the bot.

## Configuration
The `chat_id_file_directory` dictionary should be configured as follows:

```python
chat_id_file_directory = {
    "test_image": {
        "type": "image",
        'chat_id': YOUR_CHAT_ID,
        'directory': 'relative/path/to/your/image/directory'
    },
    "test_document": {
        "type": "document",
        'chat_id': YOUR_CHAT_ID,
        'directory': 'relative/path/to/your/document/directory'
    },
}
