import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

class TutorialDatabase:
    """Simple SQLite database for storing tutorial conversations."""
    
    def __init__(self, db_path: str = "database/tutorial_agent.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'chat',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_conversation(self, session_id: str, subject: str) -> int:
        """Create a new conversation and return its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (session_id, subject)
            VALUES (?, ?)
        ''', (session_id, subject))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def add_message(self, conversation_id: int, role: str, content: str, message_type: str = "chat"):
        """Add a message to the conversation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (conversation_id, role, content, message_type)
            VALUES (?, ?, ?, ?)
        ''', (conversation_id, role, content, message_type))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Get all messages for a conversation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content, message_type, timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        ''', (conversation_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "role": row[0],
                "content": row[1],
                "message_type": row[2],
                "timestamp": row[3]
            })
        
        conn.close()
        return messages
    
    def get_conversations_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, subject, created_at
            FROM conversations
            WHERE session_id = ?
            ORDER BY created_at DESC
        ''', (session_id,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                "id": row[0],
                "subject": row[1],
                "created_at": row[2]
            })
        
        conn.close()
        return conversations
    
    # Bookmark Methods
    def add_bookmark(self, conversation_id: int, message_index: int, content: str, subject: str, session_id: str, note: str = ""):
        """Add a bookmark for a specific message."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bookmarks (conversation_id, message_index, message_content, subject, session_id, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (conversation_id, message_index, content, subject, session_id, note))
        
        bookmark_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return bookmark_id
    
    def get_bookmarks(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all bookmarks for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, conversation_id, message_index, message_content, subject, created_at, note
            FROM bookmarks
            WHERE session_id = ?
            ORDER BY created_at DESC
        ''', (session_id,))
        
        bookmarks = []
        for row in cursor.fetchall():
            bookmarks.append({
                "id": row[0],
                "conversation_id": row[1],
                "message_index": row[2],
                "content": row[3],
                "subject": row[4],
                "created_at": row[5],
                "note": row[6]
            })
        
        conn.close()
        return bookmarks
    
    def remove_bookmark(self, bookmark_id: int):
        """Remove a bookmark."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
        
        conn.commit()
        conn.close()
    
    def is_bookmarked(self, conversation_id: int, message_index: int) -> bool:
        """Check if a message is bookmarked."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM bookmarks
            WHERE conversation_id = ? AND message_index = ?
        ''', (conversation_id, message_index))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    # Search Methods
    def search_conversations(self, session_id: str, query: str) -> List[Dict[str, Any]]:
        """Search across all messages in user's conversations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.content, m.role, m.timestamp, c.subject, c.id, m.id
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.session_id = ? AND m.content LIKE ?
            ORDER BY m.timestamp DESC
            LIMIT 50
        ''', (session_id, f'%{query}%'))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "content": row[0],
                "role": row[1],
                "timestamp": row[2],
                "subject": row[3],
                "conversation_id": row[4],
                "message_id": row[5]
            })
        
        conn.close()
        return results
    
    # Analytics Methods
    def get_study_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get study statistics for dashboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total conversations
        cursor.execute('''
            SELECT COUNT(*) FROM conversations WHERE session_id = ?
        ''', (session_id,))
        total_conversations = cursor.fetchone()[0]
        
        # Unique subjects
        cursor.execute('''
            SELECT COUNT(DISTINCT subject) FROM conversations WHERE session_id = ?
        ''', (session_id,))
        unique_subjects = cursor.fetchone()[0]
        
        # Total messages
        cursor.execute('''
            SELECT COUNT(*) FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.session_id = ?
        ''', (session_id,))
        total_messages = cursor.fetchone()[0]
        
        # Recent activity (last 7 days)
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM conversations
            WHERE session_id = ? AND created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''', (session_id,))
        
        recent_activity = []
        for row in cursor.fetchall():
            recent_activity.append({
                "date": row[0],
                "count": row[1]
            })
        
        conn.close()
        
        return {
            "total_conversations": total_conversations,
            "unique_subjects": unique_subjects,
            "total_messages": total_messages,
            "recent_activity": recent_activity
        }
    
    def get_topic_breakdown(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation count by subject."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT subject, COUNT(*) as count
            FROM conversations
            WHERE session_id = ?
            GROUP BY subject
            ORDER BY count DESC
            LIMIT 10
        ''', (session_id,))
        
        topics = []
        for row in cursor.fetchall():
            topics.append({
                "subject": row[0],
                "count": row[1]
            })
        
        conn.close()
        return topics 

    def get_user_stats(self, session_id: str) -> Dict[str, Any]:
        """Aggregate stats for the dashboard (API compatibility layer)."""
        stats = self.get_study_statistics(session_id)
        topics = self.get_topic_breakdown(session_id)
        
        # Format subjects as a dictionary for app.py
        subjects_dict = {t['subject']: t['count'] for t in topics}
        
        return {
            "total_conversations": stats['total_conversations'],
            "total_messages": stats['total_messages'],
            "subjects": subjects_dict
        } 