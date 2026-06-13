# layer7_api_ui/migration_manager.py
import sqlite3
import os
import re
from datetime import datetime

# Path resolution relative to this file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "layer4_agent", "app", "memory", "honeypot_conversations.db")
MIGRATIONS_DIR = os.path.join(PROJECT_ROOT, "layer7_api_ui", "migrations")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_migrations_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_applied_migrations():
    setup_migrations_table()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC")
    versions = [row["version"] for row in cursor.fetchall()]
    conn.close()
    return versions

def execute_sql_statement(cursor, statement):
    # Strip comments and clean up
    statement = statement.strip()
    if not statement:
        return
    
    try:
        cursor.execute(statement)
    except sqlite3.OperationalError as e:
        # Ignore duplicate column errors during ALTER TABLE operations
        error_msg = str(e).lower()
        if "duplicate column name" in error_msg or "already exists" in error_msg:
            print(f"   [Migration Info] Skipping column addition (already exists): {statement}")
        else:
            raise e

def apply_migration(version, filename):
    filepath = os.path.join(MIGRATIONS_DIR, filename)
    with open(filepath, "r") as f:
        sql = f.read()

    # Split statements by semicolon, avoiding splitting on functions or comments if possible
    # A simple regex split on semicolon followed by newline is usually sufficient for standard SQL
    statements = sql.split(";")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"⚙️ Applying migration {version:03d}: {filename}...")
    try:
        for stmt in statements:
            execute_sql_statement(cursor, stmt)
            
        cursor.execute("""
            INSERT INTO schema_migrations (version, name, applied_at)
            VALUES (?, ?, ?)
        """, (version, filename, datetime.now().isoformat()))
        conn.commit()
        print(f"✅ Migration {version:03d} applied successfully.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to apply migration {version:03d} ({filename}): {e}")
        raise e
    finally:
        conn.close()

def run_migrations():
    """Runs all pending migrations sequentially."""
    print("🚀 Initializing Database Migration Check...")
    if not os.path.exists(MIGRATIONS_DIR):
        print(f"❌ Migrations directory not found at: {MIGRATIONS_DIR}")
        return
        
    applied = get_applied_migrations()
    
    files = []
    for f in os.listdir(MIGRATIONS_DIR):
        match = re.match(r"^(\d+)_.*\.sql$", f)
        if match:
            files.append((int(match.group(1)), f))
            
    files.sort(key=lambda x: x[0])
    
    applied_count = 0
    for version, filename in files:
        if version not in applied:
            apply_migration(version, filename)
            applied_count += 1
            
    if applied_count == 0:
        print("🟢 Database is up-to-date. No pending migrations.")
    else:
        print(f"🎉 Migrations completed. Applied {applied_count} script(s).")

if __name__ == "__main__":
    run_migrations()
