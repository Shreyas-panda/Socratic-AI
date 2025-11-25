"""
PDF Export utility for exporting conversation history
"""

from fpdf import FPDF
from datetime import datetime
from typing import List, Dict, Any
import io
import re

class ConversationPDF(FPDF):
    """Custom PDF class for conversation export."""
    
    def __init__(self, subject: str, date: str):
        super().__init__()
        self.subject = subject
        self.date = date
        
    def header(self):
        """Add header to each page."""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, f'Socratic - {self.subject}', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, f'Exported on: {self.date}', 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        """Add footer to each page."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def remove_emojis(text: str) -> str:
    """Remove emojis and other special unicode characters from text."""
    # Remove emojis and special characters
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def export_conversation_to_pdf(subject: str, chat_history: List[Dict[str, Any]]) -> bytes:
    """
    Export a conversation to PDF format.
    
    Args:
        subject: The conversation subject/topic
        chat_history: List of message dictionaries with 'role' and 'content'
    
    Returns:
        PDF file as bytes
    """
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Clean subject from emojis
    clean_subject = remove_emojis(subject)
    
    # Create PDF
    pdf = ConversationPDF(clean_subject, current_date)
    pdf.add_page()
    
    # Add messages
    for idx, message in enumerate(chat_history, 1):
        role = message.get('role', 'unknown')
        content = message.get('content', '')
        
        # Remove emojis from content
        clean_content = remove_emojis(content)
        
        # Format based on role
        if role == 'user':
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(220, 240, 255)  # Light blue
            pdf.cell(0, 8, 'You:', 0, 1, 'L', True)
        else:
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(240, 255, 240)  # Light green
            pdf.cell(0, 8, 'Socratic AI:', 0, 1, 'L', True)
        
        # Add message content
        pdf.set_font('Arial', '', 10)
        # Handle latin-1 encoding
        try:
            pdf.multi_cell(0, 5, clean_content)
        except:
            # Fallback for problematic characters
            safe_content = clean_content.encode('ascii', 'ignore').decode('ascii')
            pdf.multi_cell(0, 5, safe_content)
        pdf.ln(3)
    
    # Get PDF as bytes (convert bytearray to bytes for Streamlit)
    return bytes(pdf.output())


def create_pdf_download_name(subject: str) -> str:
    """Generate a filename for the PDF."""
    date_str = datetime.now().strftime('%Y%m%d')
    # Clean subject for filename
    safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_subject = safe_subject.replace(' ', '_')
    return f"Socratic_{safe_subject}_{date_str}.pdf"

