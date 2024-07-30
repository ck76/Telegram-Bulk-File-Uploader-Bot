import logging
import os
import asyncio
import sqlite3
from telegram import Bot, InputMediaDocument, InputMediaPhoto
from telegram.error import TimedOut, RetryAfter

# TODO
# 0. Create a bot and get the token from BotFather, invite the bot to your group, promote the bot to admin
# 1. Replace the TOKEN with your bot token
# 2. Replace the root_directory with your root directory
# 3. Get the chat_id of your group, replace the chat_id in chat_id_file_directory
# Send GET request to https://api.telegram.org/bot{YOUT_BOT_TOKEN}}/getUpdates
# Get the chat_id from the response(json)
# 4. Replace the chat_id in chat_id_file_directory with your chat_id


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO replace with your bot token
TOKEN = "YOUR_BOT_TOKEN"

root_directory = 'YOUR_ROOT_DIRECTORY'

# chat_id file_directory key pair
chat_id_file_directory = {
    "test_image": {
        "type": "image",
        # TODO replace with your chat_id
        'chat_id': 11111111111111,
        'directory': 'testtele'
    },
    "test_document": {
        "type": "document",
        'chat_id': -111111111111111111111,
        # TODO replace with your chat_id
        'directory': 'testtele'
    },
}

bot = Bot(token=TOKEN)


def get_files(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]


def get_image_files(directory):
    supported_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(supported_extensions)]


def get_video_files(directory):
    supported_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(supported_extensions)]


def get_audio_files(directory):
    supported_extensions = ('.mp3', '.wav', '.flac', '.aac')
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(supported_extensions)]


async def send_file_to_chat(chat_id: int, file_path: str, retries=3):
    """send file to chat with retries, default retries is 3 times"""
    try:
        with open(file_path, 'rb') as file:
            await bot.send_document(chat_id=chat_id, document=file, read_timeout=60, write_timeout=60,
                                    connect_timeout=60, pool_timeout=60)
        return True
    except TimedOut:
        if retries > 0:
            logger.error(f"Request timed out when sending file {file_path}, retrying... {retries} retries left")
            return await send_file_to_chat(chat_id, file_path, retries - 1)
        else:
            logger.error(f"Request timed out when sending file {file_path}, no retries left")
            await bot.send_message(chat_id=chat_id, text=f"Failed to send file {file_path} due to timeout.")
    except Exception as e:
        logger.error(f"Error sending file {file_path}: {e}")
        await bot.send_message(chat_id=chat_id, text=f"Failed to send file {file_path} due to error: {e}")
    return False


async def send_media_group_to_chat(chat_id: int, media_group, retries=3):
    """send media group to chat with retries, default retries is 3 times"""
    try:
        await bot.send_media_group(chat_id=chat_id, media=media_group, read_timeout=60, write_timeout=60,
                                   connect_timeout=60, pool_timeout=60)
        return True
    except RetryAfter as e:
        if retries > 0:
            retry_after = e.retry_after
            logger.error(f"Flood control exceeded. Retry in {retry_after} seconds, {retries} retries left")
            await asyncio.sleep(retry_after)
            return await send_media_group_to_chat(chat_id, media_group, retries - 1)
        else:
            logger.error(f"Flood control exceeded. No retries left")
            await bot.send_message(chat_id=chat_id, text="Failed to send media group due to flood control.")
    except TimedOut:
        if retries > 0:
            logger.error(f"Request timed out when sending media group, retrying... {retries} retries left")
            return await send_media_group_to_chat(chat_id, media_group, retries - 1)
        else:
            logger.error(f"Request timed out when sending media group, no retries left")
            await bot.send_message(chat_id=chat_id, text="Failed to send media group due to timeout.")
    except Exception as e:
        logger.error(f"Error sending media group: {e}")
        await bot.send_message(chat_id=chat_id, text=f"Failed to send media group due to error: {e}")
    return False


# 主函数
async def main():
    # sqlite connection
    conn = sqlite3.connect('telegram.db')
    c = conn.cursor()

    for chat, chat_info in chat_id_file_directory.items():
        batch_size = 10
        chat_id = chat_info['chat_id']
        file_type = chat_info['type']
        file_directory = os.path.join(root_directory, chat_info['directory'])
        # if file_directory not exists, skip
        if not os.path.exists(file_directory):
            logger.error(f"File directory {file_directory} does not exist, skipping...")
            continue
        # use chat_id as table_name
        table_name = str(chat)
        logger.info(
            f"Processing chat {chat} with chat_id {chat_id} and file_directory {file_directory} and file_type {file_type}")
        logger.info(f"Creating table {table_name} if not exists")
        # table columns: id, file_name(string), file_meta_data(string), media_uploaded(bool),document_uploaded(bool)
        c.execute(
            f'''CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT, file_meta_data TEXT, media_uploaded BOOLEAN, document_uploaded BOOLEAN)''')

        # if file_type == "image": call send_media_group_to_chat and call send_file_to_chat
        # because I want to save image twice, one for media, one for document(because document type is not compressed)
        # if record exists, update media_uploaded to True
        # if record not exists, insert record into table
        if file_type == "image":
            files = get_image_files(file_directory)
            # use pure file name, so remove file_directory
            files = [os.path.basename(file) for file in files]
            logger.info(f"Files-file_type ==image: {files}")
            # sort files by name, from small to large, alphabetical order a to z
            files.sort()

            # filter out files that have not been uploaded(media_uploaded == false)
            not_uploaded_images = [photo for photo in files if not c.execute(
                f"SELECT * FROM {table_name} WHERE file_name = '{photo}' AND media_uploaded = 0").fetchone()]
            logger.info(f"not_uploaded_images: {not_uploaded_images}")
            for i in range(0, len(not_uploaded_images), batch_size):
                batch = not_uploaded_images[i:i + batch_size]
                logger.info(f"Sending batch {i // batch_size + 1} of {len(not_uploaded_images) // batch_size + 1}")
                logger.info(f"Batch: {batch}")
                media_group = [InputMediaPhoto(open(os.path.join(file_directory, photo), 'rb')) for photo in batch]
                if await send_media_group_to_chat(chat_id, media_group):
                    # If success, update record in table, if record not exists, insert record into table, if record exists, update media_uploaded to True
                    for img_i in batch:
                        if c.execute(f"SELECT * FROM {table_name} WHERE file_name = '{img_i}'").fetchone() is None:
                            c.execute(
                                f"INSERT INTO {table_name} (file_name, media_uploaded, document_uploaded) VALUES ('{img_i}', 1, 0)")
                        else:
                            c.execute(
                                f"UPDATE {table_name} SET media_uploaded = 1 WHERE file_name = '{img_i}'")
                    conn.commit()
                await asyncio.sleep(5)

            # filter out files that have not been uploaded(document_uploaded == false)
            not_uploaded_documents = [photo for photo in files if not c.execute(
                f"SELECT * FROM {table_name} WHERE file_name = '{photo}' AND document_uploaded = 0").fetchone()]
            logger.info(f"not_uploaded_documents: {not_uploaded_documents}")
            for i in range(0, len(not_uploaded_documents), batch_size):
                logger.info(f"Sending batch {i // batch_size + 1} of {len(not_uploaded_documents) // batch_size + 1}")
                logger.info(f"Batch: {batch}")
                batch = not_uploaded_documents[i:i + batch_size]
                media_group = [InputMediaDocument(open(os.path.join(file_directory, photo), 'rb')) for photo in batch]
                if await send_media_group_to_chat(chat_id, media_group):
                    for doc_i in batch:
                        if c.execute(f"SELECT * FROM {table_name} WHERE file_name = '{doc_i}'").fetchone() is None:
                            c.execute(
                                f"INSERT INTO {table_name} (file_name, media_uploaded, document_uploaded) VALUES ('{doc_i}', 0, 1)")
                        else:
                            c.execute(
                                f"UPDATE {table_name} SET document_uploaded = 1 WHERE file_name = '{doc_i}'")
                    conn.commit()
                await asyncio.sleep(5)

        if file_type == "document":
            files = get_files(file_directory)
            # use pure file name, so remove file_directory
            files = [os.path.basename(file) for file in files]
            # sort files by name, from small to large, alphabetical order a to z
            files.sort()
            not_uploaded_documents = [document for document in files if not c.execute(
                f"SELECT * FROM {table_name} WHERE file_name = '{document}' AND document_uploaded = 0").fetchone()]
            logger.info(f"not_uploaded_documents: {not_uploaded_documents}")
            for i in range(0, len(not_uploaded_documents), batch_size):
                batch = not_uploaded_documents[i:i + batch_size]
                logger.info(f"Sending batch {i // batch_size + 1} of {len(not_uploaded_documents) // batch_size + 1}")
                logger.info(f"Batch: {batch}")
                media_group = [InputMediaDocument(open(os.path.join(file_directory, photo), 'rb')) for photo in batch]
                if await send_media_group_to_chat(chat_id, media_group):
                    for doc_i in batch:
                        if c.execute(f"SELECT * FROM {table_name} WHERE file_name = '{doc_i}'").fetchone() is None:
                            c.execute(
                                f"INSERT INTO {table_name} (file_name, media_uploaded, document_uploaded) VALUES ('{doc_i}', 0, 1)")
                        else:
                            c.execute(
                                f"UPDATE {table_name} SET document_uploaded = 1 WHERE file_name = '{doc_i}'")
                    conn.commit()
                await asyncio.sleep(5)
        logger.info(f"Finished processing chat {chat} with chat_id {chat_id} and file_directory {file_directory}")
    logger.info("Finished processing all chats")
    conn.close()


if __name__ == '__main__':
    asyncio.run(main())
