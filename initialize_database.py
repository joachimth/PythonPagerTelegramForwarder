import sqlite3
from configparser import ConfigParser
import logging

# Logger opsætning
LOG_FILE = "initialize_database.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Log til fil
        logging.StreamHandler()        # Log til konsol
    ]
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
    logger.info("Databasen er blevet initialiseret.")

def insert_dummy_messages():
    """
    Indsætter dummy-beskeder fra config.txt i databasen.
    """
    cfg = load_config()

    # Tjek om dummy-data er aktiveret
    if not cfg.getboolean("DummyData", "enable_dummy_data", fallback=False):
        logger.info("Dummy-beskeder er deaktiveret i config.txt.")
        return

    dummy_messages = cfg.get("DummyData", "dummy_messages", fallback="").split("\n")
    dummy_messages = [msg.strip() for msg in dummy_messages if msg.strip()]

    if not dummy_messages:
        logger.info("Ingen dummy-beskeder fundet i config.txt.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for message in dummy_messages:
            cursor.execute("""
                INSERT INTO messages (raw_message)
                VALUES (?)
            """, (message,))
        conn.commit()
    logger.info("Dummy-beskeder er blevet indsat i databasen.")

if __name__ == "__main__":
    initialize_database()
    insert_dummy_messages()