import os
import json
import requests
from loguru import logger
from fetch_texts import fetch_texts
from utils import (
    get_random_voice_speed,
    get_random_voice_for_server,
    initialize_database,
    save_text_to_database,
    save_metadata_to_database,
    has_voice
)

# Configure logging
logger.remove()
logger.add("logs/tts_processing.log", rotation="10 MB", level="INFO")

# Load configuration
with open("config.json", "r") as config_file:
    config = json.load(config_file)

TTS_SERVERS = config["tts_servers"]
AUDIO_DIR = config["output_dir"]["audio"]


def send_tts_request(server, text, voice, speed):
    """
    Sends a TTS request to the specified server.
    :param server: Dictionary containing server details.
    :param text: The text to convert to speech.
    :param voice: voice for the TTS.
    :param speed: Speech speed.
    :return: Response from the TTS server.
    """
    payload = {
        "input": text,
        "model": server["model"],
        "voice": voice,
        "speed": speed,
        "response_format": "mp3"
    }

    response = requests.post(server["url"], headers=server["headers"], json=payload)
    if response.status_code != 200:
        logger.error(f"TTS Server Error ({server['url']}): {response.status_code} - {response.text}")
        raise Exception(f"TTS Server Error ({server['url']}): {response.status_code} - {response.text}")
    return response


def process_text(text_id, text, server):
    """
    Processes a single text by generating audio files for all compatible server combinations.
    :param text_id: Unique ID of the text.
    :param text: Input text.
    :param server: server.
    """
    try:
        voice = get_random_voice_for_server(server)
        speed = get_random_voice_speed()
        # Send TTS request
        response = send_tts_request(server, text, voice, speed)

        # Save audio file
        audio_filename = f"{text_id}_{server['name']}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        with open(audio_path, "wb") as audio_file:
            audio_file.write(response.content)

        # Save metadata to database
        save_metadata_to_database(text_id, server["name"], voice, speed, audio_filename)

        logger.info(
            f"Processed: {text_id}... (Voice: {voice}, Speed: {speed}) on {server['name']}"
        )
    except Exception as e:
        logger.error(f"Error processing text: {text_id}... ({e})")


def main():
    # Initialize database
    initialize_database()

    # Fetch texts using the custom module
    logger.info("Starting text processing...")
    for text_id, text in fetch_texts():
        logger.info(f"Processing text: (ID: {text_id}) {text[:50]}...")
        save_text_to_database(text_id, text)
        # Generate all possible combinations for each server
        for server in TTS_SERVERS:
            if has_voice(text_id, server["name"]):
                logger.info(f"Skipping completed: (ID: {text_id}) (engine: {server['name']})")
                continue
            process_text(text_id, text, server)

    logger.info("Text processing completed.")


if __name__ == "__main__":
    main()