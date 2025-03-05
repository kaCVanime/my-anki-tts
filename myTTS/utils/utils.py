import sqlite3
import random

DB_PATH="tts_database.db"

def get_random_voice_speed():
    return random.choices(
        [0.9, 1.0, 1.1],
        weights=[1, 7.5, 1.5],
        k=1
    )[0]

def get_random_voice_for_server(server):
    return random.choice(server["voices"])


def initialize_database():
    """
    Initializes the SQLite3 database and creates the tables if they don't exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table for storing unique texts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS texts (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL
        )
    """)

    # Table for storing metadata linked to texts via foreign key
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tts_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_id TEXT NOT NULL,
            engine TEXT NOT NULL,
            voice TEXT NOT NULL,
            speed REAL NOT NULL,
            audio_file TEXT NOT NULL,
            FOREIGN KEY (text_id) REFERENCES texts(id)
        )
    """)
    cursor.execute(
        """
            CREATE INDEX IF NOT EXISTS idx_text
            ON texts (text);
        """
    )
    cursor.execute(
        """
            CREATE INDEX IF NOT EXISTS idx_text_id
            ON tts_metadata (text_id);
        """
    )
    cursor.execute(
        """
            CREATE INDEX IF NOT EXISTS idx_voice
            ON tts_metadata (voice);
        """
    )
    cursor.execute(
        """
            CREATE INDEX IF NOT EXISTS idx_speed
            ON tts_metadata (speed);
        """
    )
    conn.commit()
    conn.close()


def save_text_to_database(text_id, text):
    """
    Saves a text to the database if it doesn't already exist.
    :param text_id: Unique ID of the text.
    :param text: The text content.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO texts (id, text) VALUES (?, ?)
    """, (text_id, text))
    conn.commit()
    conn.close()


def save_metadata_to_database(text_id, engine, voice, speed, audio_file):
    """
    Saves metadata to the SQLite3 database.
    :param text_id: Unique ID of the text.
    :param engine: server engine.
    :param voice: Character voice used for TTS.
    :param speed: Speech speed used for TTS.
    :param audio_file: Filename of the generated audio file.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tts_metadata (text_id, engine, voice, speed, audio_file)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (text_id, engine, voice, speed, audio_file))
    conn.commit()
    conn.close()

def get_all_text_ids():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT id
                FROM texts
            """
        )
        result = cursor.fetchall()
        return [row[0] for row in result]

def has_voice(text_id, engine):
    """
    Check a text has a voice or not
    :param text_id: Unique ID of the text.
    :param engine: tts engine of voice
    :return:
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM tts_metadata
        WHERE text_id = ? AND engine = ?
        LIMIT 1
    """, (text_id, engine))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def reuse_audio(text_id, text):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                    SELECT id
                    FROM texts
                    WHERE text = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                """
            , (text,))
            row = cursor.fetchone()
            if row is not None:
                id = row[0]
                cursor.execute(
                    """
                        INSERT INTO tts_metadata (text_id, engine, voice, speed, audio_file)
                        SELECT ?, engine, voice, speed, audio_file
                        FROM tts_metadata
                        WHERE text_id = ?
                        ORDER BY RANDOM()
                        LIMIT 1;
                    """
                    , (text_id, id)
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e