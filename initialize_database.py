import sqlite3

DB_PATH = "messages.db"

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
        parsed_fields TEXT
    )
    """)

    conn.commit()
    conn.close()

def insert_test_data():
    """
    Indsætter testdata i databasen for at sikre, at der er nogle beskeder at arbejde med.
    """
    test_data = [
        {"raw_message": "Test besked 1", "parsed_fields": None},
        {"raw_message": "Test besked 2", "parsed_fields": None},
    ]
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for data in test_data:
            cursor.execute("""
                INSERT INTO messages (raw_message, parsed_fields)
                VALUES (?, ?)
            """, (data["raw_message"], data["parsed_fields"]))
        conn.commit()
    print("Testdata indsat i databasen.")

if __name__ == "__main__":
    initialize_database()
    insert_test_data()