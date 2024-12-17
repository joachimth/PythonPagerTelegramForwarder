import sqlite3

def initialize_database(db_path='messages.db'):
    """
    Initialiserer SQLite-databasen og opretter `messages`-tabellen.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        raw_message TEXT NOT NULL,
        parsed_fields TEXT DEFAULT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database '{db_path}' initialiseret og klar til brug.")

if __name__ == "__main__":
    initialize_database()