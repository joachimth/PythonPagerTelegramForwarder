import sqlite3
import logging
from configparser import ConfigParser

# Logger opsætning
logging.basicConfig(
    filename="initialize_database.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("initialize_database")

DB_PATH = "messages.db"

def load_config(filepath='config.txt'):
    """
    Indlæser konfigurationsindstillinger fra config.txt.
    """
    cfg = ConfigParser()
    cfg.read(filepath)
    return cfg

def initialize_database():
    """
    Initialiserer SQLite-databasen og opretter `messages`-tabellen.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        raw_message TEXT NOT NULL,
        parsed_fields TEXT,
        sent_to_telegram INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialiseret.")

def insert_dummy_data(cfg):
    """
    Indsætter dummy-data i databasen, hvis det er aktiveret i config.txt.
    """
    if cfg.getboolean("DummyData", "enable_dummy_data", fallback=False):
        dummy_messages = cfg.get("DummyData", "dummy_messages", fallback="").split("\n")
        dummy_messages = [msg.strip() for msg in dummy_messages if msg.strip()]

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for message in dummy_messages:
                cursor.execute("""
                    INSERT INTO messages (raw_message)
                    VALUES (?)
                """, (message,))
            conn.commit()
        logger.info(f"{len(dummy_messages)} dummy-beskeder indsat i databasen.")

if __name__ == "__main__":
    config = load_config()
    initialize_database()
    insert_dummy_data(config)