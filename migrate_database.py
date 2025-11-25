"""
Database migration script for adding new features:
- Bookmarks table
- Image support columns in messages table
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Run database migrations."""
    db_path = os.path.join("database", "tutorial_agent.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Creating new database...")
        os.makedirs("database", exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # Create bookmarks table
    print("Creating bookmarks table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            message_index INTEGER NOT NULL,
            message_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subject TEXT,
            note TEXT,
            session_id TEXT
        )
    """)
    
    # Check if messages table has image columns
    cursor.execute("PRAGMA table_info(messages)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'image_path' not in columns:
        print("Adding image_path column to messages table...")
        cursor.execute("ALTER TABLE messages ADD COLUMN image_path TEXT")
    
    if 'has_image' not in columns:
        print("Adding has_image column to messages table...")
        cursor.execute("ALTER TABLE messages ADD COLUMN has_image BOOLEAN DEFAULT 0")
    
    # Create index for faster bookmark queries
    print("Creating indexes...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookmarks_session 
        ON bookmarks(session_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookmarks_conversation 
        ON bookmarks(conversation_id)
    """)
    
    # Create index for search performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_content 
        ON messages(content)
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Database migration completed successfully!")
    print(f"Migration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    migrate_database()
