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
        stednavn TEXT,
        adresse TEXT,
        postnr TEXT,
        by TEXT,
        lat TEXT,
        long TEXT,
        linktilgooglemaps TEXT,
        alarmtype_kritisk BOOLEAN,
        alarmtype_seriøs BOOLEAN,
        alarmtype_lavrisiko BOOLEAN,
        alarmtype_højrisiko BOOLEAN,
        alarmkald_politi BOOLEAN,
        alarmkald_brand BOOLEAN,
        alarmkald_isl BOOLEAN,
        alarmkald_medicin BOOLEAN,
        alarmkald_vagt BOOLEAN,
        alarmkald_specialrespons BOOLEAN,
        specifik_brandalarm BOOLEAN,
        specifik_gasledningsbrud BOOLEAN,
        specifik_bygningsbrand BOOLEAN
    )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()