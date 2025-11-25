import streamlit as st
import uuid
from datetime import datetime
from tutorial_agent import TutorialAgent
from database import TutorialDatabase
import sqlite3
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import io
from pdf_export import export_conversation_to_pdf, create_pdf_download_name
from image_handler import save_uploaded_image, analyze_image_with_llm
import altair as alt
import pandas as pd


# Configure the Streamlit page
st.set_page_config(
    page_title="Socratic - AI Tutor",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme Configurations
THEMES = {
    "Nordic Light": {
        "bg_color": "#f0f2f6",
        "sidebar_bg": "#ffffff",
        "text_color": "#1e293b",
        "accent_color": "#2563eb",
        "card_bg": "#ffffff",
        "chat_user_bg": "#e0f2fe",
        "chat_bot_bg": "#ffffff",
        "border_color": "#e2e8f0"
    },
    "Midnight Pro": {
        "bg_color": "#0f172a",
        "sidebar_bg": "#1e293b",
        "text_color": "#e2e8f0",
        "accent_color": "#38bdf8",
        "card_bg": "#1e293b",
        "chat_user_bg": "#334155",
        "chat_bot_bg": "#1e293b",
        "border_color": "#334155"
    }
}

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "agent" not in st.session_state:
    st.session_state.agent = TutorialAgent()

if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "subject" not in st.session_state:
    st.session_state.subject = ""

if "theme" not in st.session_state:
    st.session_state.theme = "Midnight Pro"  # Dark mode by default


if "language" not in st.session_state:
    st.session_state.language = "English"

if "is_temporary_mode" not in st.session_state:
    st.session_state.is_temporary_mode = False

if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = None

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "chat"  # Options: "chat", "dashboard"

if "bookmarked_messages" not in st.session_state:
    st.session_state.bookmarked_messages = set()  # Set of (conversation_id, message_index) tuples

if "search_query" not in st.session_state:
    st.session_state.search_query = ""


def apply_theme(theme_name):
    """Inject CSS for the selected theme."""
    theme = THEMES[theme_name]
    
    st.markdown(f"""
    <style>
        /* Main Layout */
        .stApp {{
            background-color: {theme['bg_color']};
            color: {theme['text_color']};
        }}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: {theme['sidebar_bg']};
            border-right: 1px solid {theme['border_color']};
        }}
        
        /* Text Styling */
        h1, h2, h3, h4, h5, h6, p, li {{
            color: {theme['text_color']} !important;
            font-family: 'Inter', sans-serif;
        }}
        
        /* Chat Message Styling */
        .stChatMessage {{
            background-color: transparent;
        }}
        
        [data-testid="stChatMessageContent"] {{
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        /* User Message */
        div[data-testid="stChatMessage"]:nth-child(odd) [data-testid="stChatMessageContent"] {{
            background-color: {theme['chat_user_bg']};
            border: 1px solid {theme['border_color']};
        }}
        
        /* Bot Message */
        div[data-testid="stChatMessage"]:nth-child(even) [data-testid="stChatMessageContent"] {{
            background-color: {theme['chat_bot_bg']};
            border: 1px solid {theme['border_color']};
        }}
        
        /* Button Styling */
        .stButton button {{
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, {theme['card_bg']} 0%, {theme['sidebar_bg']} 100%);
            color: {theme['text_color']};
            border: 2px solid {theme['border_color']};
            padding: 0.6rem 1.2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }}
        .stButton button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            border-color: {theme['accent_color']};
            background: linear-gradient(135deg, {theme['accent_color']}15 0%, {theme['accent_color']}25 100%);
            color: {theme['accent_color']};
        }}
        .stButton button:active {{
            transform: translateY(-1px);
            box-shadow: 0 3px 6px rgba(0,0,0,0.12);
        }}
        
        /* Form Submit Button Fix */
        [data-testid="stFormSubmitButton"] button {{
            background: linear-gradient(135deg, {theme['accent_color']} 0%, {theme['accent_color']}dd 100%) !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 4px 8px {theme['accent_color']}40 !important;
            font-weight: 700 !important;
        }}
        [data-testid="stFormSubmitButton"] button:hover {{
            opacity: 0.9;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px {theme['accent_color']}60 !important;
        }}
        
        /* Welcome Card */
        .welcome-card {{
            background-color: {theme['card_bg']};
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            text-align: center;
            height: 100%;
            border: 1px solid {theme['border_color']};
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .welcome-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0,0,0,0.1);
            border-color: {theme['accent_color']};
        }}
        
        /* Input Field */
        .stChatInputContainer {{
            padding-bottom: 20px;
        }}
        
        /* Microphone Button Styling */
        .mic-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            padding-top: 8px;
        }}
        
        /* Custom microphone button styles - more specific selector */
        .mic-container button {{
            border-radius: 50% !important;
            width: 48px !important;
            height: 48px !important;
            padding: 0 !important;
            background: linear-gradient(135deg, {theme['accent_color']} 0%, {theme['accent_color']}dd 100%) !important;
            border: 2px solid {theme['accent_color']} !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
            transition: all 0.3s ease !important;
        }}
        
        .mic-container button:hover {{
            transform: scale(1.1) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25) !important;
        }}
        
        /* Recording animation */
        @keyframes pulse {{
            0%, 100% {{
                opacity: 1;
                transform: scale(1);
            }}
            50% {{
                opacity: 0.8;
                transform: scale(1.05);
            }}
        }}
        
        /* Temporary Mode Badge */
        .temp-mode-badge {{
            background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            margin: 10px 0;
            text-align: center;
            box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
            animation: pulse 2s ease-in-out infinite;
        }}
        
        /* New Chat Button - Enhanced Styling */
        div[data-testid="stSidebar"] .stButton:has(button[kind="primary"]) button,
        div[data-testid="stSidebar"] button:contains("New Chat") {{
            background: linear-gradient(135deg, {theme['accent_color']}20 0%, {theme['accent_color']}35 100%) !important;
            border: 2px solid {theme['accent_color']} !important;
            color: {theme['text_color']} !important;
            font-weight: 700 !important;
            box-shadow: 0 3px 8px {theme['accent_color']}30 !important;
        }}
        
        div[data-testid="stSidebar"] .stButton:has(button[kind="primary"]) button:hover {{
            background: linear-gradient(135deg, {theme['accent_color']} 0%, {theme['accent_color']}ee 100%) !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 14px {theme['accent_color']}50 !important;
        }}
        
        /* Hide Streamlit Branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
    </style>
    """, unsafe_allow_html=True)

def start_new_chat():
    """Start a new chat, clearing the current conversation."""
    st.session_state.current_conversation_id = None
    st.session_state.subject = ""
    st.session_state.chat_history = []
    st.rerun()

def toggle_bookmark(conversation_id, message_index, content, subject):
    """Toggle bookmark for a message."""
    db = TutorialDatabase()
    bookmark_key = (conversation_id, message_index)
    
    if bookmark_key in st.session_state.bookmarked_messages:
        # Remove bookmark
        st.session_state.bookmarked_messages.remove(bookmark_key)
        db.remove_bookmark(bookmark_id=None)  # We'll need to look it up
        st.success("Bookmark removed!")
    else:
        # Add bookmark
        st.session_state.bookmarked_messages.add(bookmark_key)
        db.add_bookmark(
            conversation_id=conversation_id,
            message_index=message_index,
            content=content[:200],  # Store first 200 chars
            subject=subject,
            session_id=st.session_state.session_id
        )
        st.success("Message bookmarked!")

def handle_image_upload(uploaded_file, user_question=""):
    """Handle image upload and analysis."""
    if uploaded_file and st.session_state.current_conversation_id:
        # Save image
        image_path = save_uploaded_image(uploaded_file, str(st.session_state.current_conversation_id))
        
        # Get AI analysis
        if not user_question:
            user_question = "Please analyze this image and explain what you see in the context of our lesson."
        
        with st.spinner("🔍 Analyzing image..."):
            response = analyze_image_with_llm(image_path, user_question, st.session_state.subject)
        
        # Add to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question,
            "type": "message",
            "image_path": image_path
        })
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "type": "response"
        })
        
        st.rerun()

def switch_view_mode(mode):
    """Switch between chat and dashboard views."""
    st.session_state.view_mode = mode
    st.rerun()


def start_new_tutorial(subject):
    """Start a new tutorial session."""
    if subject and subject.strip():
        try:
            with st.spinner(f"🏛️ Socratic is preparing your lesson on {subject}..."):
                # Generate a temporary conversation ID for temporary mode
                if st.session_state.is_temporary_mode:
                    # Create temporary conversation without saving to database
                    temp_conv_id = f"temp_{uuid.uuid4()}"
                    
                    # Get initial response using the agent
                    from tutorial_agent import TutorialAgent
                    temp_agent = TutorialAgent()
                    
                    # Manually create a conversation response without database save
                    initial_content = f"""Welcome to your lesson on **{subject.strip()}**! 

I'm Socratic, your AI tutor. I'll guide you through this topic using the Socratic method - asking questions to help you discover and understand concepts on your own.

Let's begin our exploration of {subject.strip()}. What would you like to know first, or would you like me to start with an overview?

**Note:** This is a temporary chat and won't be saved to your history."""
                    
                    st.session_state.current_conversation_id = temp_conv_id
                    st.session_state.subject = subject.strip()
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": initial_content, "type": "tutorial"}
                    ]
                else:
                    # Normal mode - save to database
                    result = st.session_state.agent.start_tutorial(
                        st.session_state.session_id, 
                        subject.strip(),
                        st.session_state.language
                    )
                    
                    # Update session state
                    st.session_state.current_conversation_id = result["conversation_id"]
                    st.session_state.subject = subject.strip()
                    st.session_state.chat_history = [
                        {"role": "assistant", "content": result["response"], "type": "tutorial"}
                    ]
                st.rerun()
            
        except Exception as e:
            st.error(f"Error starting tutorial: {str(e)}")

def handle_user_input(user_input):
    """Handle user message."""
    if user_input and st.session_state.current_conversation_id:
        # Add user message immediately
        st.session_state.chat_history.append({
            "role": "user", 
            "content": user_input,
            "type": "message"
        })
        
        # Determine input type
        input_type = "question"
        if "test me" in user_input.lower() or "quiz" in user_input.lower() or "evaluate" in user_input.lower():
            input_type = "evaluation_request"
            
        try:
            with st.spinner("🤔 Socratic is thinking..."):
                # Check if in temporary mode
                if st.session_state.is_temporary_mode or str(st.session_state.current_conversation_id).startswith("temp_"):
                    # For temporary mode, use the existing LLM API
                    from LLM_api import client
                    
                    # Build context from chat history
                    messages = [{"role": "system", "content": f"You are Socratic, an AI tutor teaching about {st.session_state.subject}. Use the Socratic method - guide students to discover answers through thoughtful questions rather than direct explanations."}]
                    
                    # Add recent chat history for context (last 5 messages)
                    for msg in st.session_state.chat_history[-5:]:
                        if msg["role"] in ["user", "assistant"]:
                            messages.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
                    
                    # Add the new user message
                    messages.append({
                        "role": "user",
                        "content": user_input
                    })
                    
                    # Get response from LLM
                    completion = client.chat.completions.create(
                        model="meta-llama/llama-4-scout",
                        messages=messages
                    )
                    
                    ai_response = completion.choices[0].message.content
                    
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": ai_response,
                        "type": "response"
                    })
                else:
                    # Normal mode with database
                    result = st.session_state.agent.continue_conversation(
                        st.session_state.current_conversation_id,
                        user_input,
                        input_type,
                        st.session_state.language
                    )
                    
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": result["response"],
                        "type": "response"
                    })
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

def transcribe_audio(audio_bytes):
    """Transcribe audio using Google Speech Recognition."""
    from pydub import AudioSegment
    
    r = sr.Recognizer()
    try:
        # Convert audio bytes to AudioSegment (handles WebM format)
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Export as WAV to a new BytesIO object
        wav_io = io.BytesIO()
        audio.export(wav_io, format='wav')
        wav_io.seek(0)
        
        # Now use SpeechRecognition on the WAV file
        with sr.AudioFile(wav_io) as source:
            audio_data = r.record(source)
            
            # Use the selected language for recognition
            language_codes = {
                "English": "en-US",
                "Hindi": "hi-IN",
                "Tamil": "ta-IN",
                "Telugu": "te-IN"
            }
            lang_code = language_codes.get(st.session_state.language, "en-US")
            
            text = r.recognize_google(audio_data, language=lang_code)
            return text
    except sr.UnknownValueError:
        st.error("Could not understand audio. Please try again.")
        return None
    except sr.RequestError as e:
        st.error(f"Could not request results; {e}")
        return None
    except Exception as e:
        st.error(f"Error processing audio: {e}")
        return None

def load_conversation(conversation_id):
    """Load a previous conversation."""
    try:
        db = TutorialDatabase()
        history = db.get_conversation_history(conversation_id)
        
        # Get conversation subject
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT subject FROM conversations WHERE id = ?", (conversation_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            st.session_state.current_conversation_id = conversation_id
            st.session_state.subject = result[0]
            st.session_state.chat_history = []
            
            # Convert database history to chat format
            for msg in history:
                role = msg["role"]
                content = msg["content"]
                msg_type = msg.get("message_type", "message")
                
                st.session_state.chat_history.append({
                    "role": role,
                    "content": content,
                    "type": msg_type
                })
            
            st.success(f"Loaded lesson: {result[0]}")
            st.rerun()
        
    except Exception as e:
        st.error(f"Error loading conversation: {str(e)}")

def main():
    """Main Streamlit application."""
    
    # Sidebar
    with st.sidebar:
        st.title("🏛️ Socratic")
        st.caption("Intelligent Tutoring System")
        
        st.markdown("---")
        
        # Language Selector
        st.subheader("🌐 Language")
        selected_language = st.selectbox(
            "Choose Language",
            ["English", "Hindi", "Tamil", "Telugu"],
            index=["English", "Hindi", "Tamil", "Telugu"].index(st.session_state.language),
            label_visibility="collapsed"
        )
        
        if selected_language != st.session_state.language:
            st.session_state.language = selected_language
            st.rerun()
            
        st.markdown("---")
        
        # Theme Toggle
        st.subheader("🎨 Appearance")
        selected_theme = st.radio(
            "Select Theme",
            ["Nordic Light", "Midnight Pro"],
            index=0 if st.session_state.theme == "Nordic Light" else 1,
            label_visibility="collapsed"
        )
        
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
            
        st.markdown("---")
        
        # Temporary Chat Toggle
        st.subheader("🔘 Chat Mode")
        temp_mode = st.checkbox(
            "Temporary Chat (not saved)", 
            value=st.session_state.is_temporary_mode,
            help="Enable this to have conversations that won't be saved to history"
        )
        
        if temp_mode != st.session_state.is_temporary_mode:
            st.session_state.is_temporary_mode = temp_mode
            st.rerun()
        
        # Show temporary mode indicator if enabled
        if st.session_state.is_temporary_mode:
            st.markdown("""
            <div class="temp-mode-badge">
                ⚠️ TEMPORARY MODE ACTIVE
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # View Mode Toggle (Dashboard/Chat)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 Chat", use_container_width=True, type="primary" if st.session_state.view_mode == "chat" else "secondary"):
                switch_view_mode("chat")
        with col2:
            if st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state.view_mode == "dashboard" else "secondary"):
                switch_view_mode("dashboard")
        
        st.markdown("---")
        
        # PDF Export (only show when conversation is active)
        if st.session_state.current_conversation_id and not str(st.session_state.current_conversation_id).startswith("temp_"):
            pdf_bytes = export_conversation_to_pdf(
                st.session_state.subject,
                st.session_state.chat_history
            )
            filename = create_pdf_download_name(st.session_state.subject)
            st.download_button(
                label="📥 Export PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )
            st.markdown("---")
        
        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True, help="Start a new conversation"):
            start_new_chat()

        
        
        st.markdown("---")
        
        # Lessons Section (moved above Search)
        st.header("📚 Lessons")
        
        # New tutorial input
        with st.form("new_tutorial_form"):
            new_subject = st.text_input(
                "What do you want to learn?",
                placeholder="e.g., Quantum Physics..."
            )
            submitted = st.form_submit_button("Start Learning 🚀", use_container_width=True)
            if submitted and new_subject:
                start_new_tutorial(new_subject)
        
        st.markdown("---")
        
        # Search History
        st.subheader("🔍 Search")
        search_query = st.text_input(
            "Search conversations...",
            value=st.session_state.search_query,
            placeholder="Type to search...",
            label_visibility="collapsed"
        )
        
        if search_query and search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
        
        if search_query:
            db = TutorialDatabase()
            results = db.search_conversations(st.session_state.session_id, search_query)
            
            if results:
                st.caption(f"Found {len(results)} results")
                for result in results[:5]:  # Show top 5
                    with st.expander(f"📄 {result['subject'][:20]}...", expanded=False):
                        st.caption(f"🕒 {result['timestamp']}")
                        st.write(result['content'][:100] + "...")
                        if st.button("Open", key=f"search_{result['message_id']}", use_container_width=True):
                            load_conversation(result['conversation_id'])
            else:
                st.info("No results found")
        
        st.markdown("---")
        
        # Bookmarks Section
        st.subheader("📑 Bookmarks")
        db = TutorialDatabase()
        bookmarks = db.get_bookmarks(st.session_state.session_id)
        
        if bookmarks:
            for bookmark in bookmarks[:5]:  # Show top 5
                with st.expander(f"⭐ {bookmark['subject'][:20]}...", expanded=False):
                    st.caption(f"🕒 {bookmark['created_at']}")
                    st.write(bookmark['content'][:100] + "...")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Open", key=f"bm_open_{bookmark['id']}", use_container_width=True):
                            load_conversation(bookmark['conversation_id'])
                    with col_b:
                        if st.button("Remove", key=f"bm_del_{bookmark['id']}", use_container_width=True):
                            db.remove_bookmark(bookmark['id'])
                            st.rerun()
        else:
            st.info("No bookmarks yet")
        
        st.markdown("---")
        
        # Previous conversations
        st.subheader("📜 History")
        try:
            db = TutorialDatabase()
            conversations = db.get_conversations_by_session(st.session_state.session_id)

            
            if conversations:
                for conv in conversations:
                    if st.button(
                        f"📝 {conv['subject'][:25]}...",
                        key=f"load_{conv['id']}",
                        use_container_width=True
                    ):
                        load_conversation(conv['id'])
            else:
                st.info("No previous lessons found.")
                
        except Exception as e:
            st.error(f"Error loading history: {str(e)}")

    # Apply Theme CSS
    apply_theme(st.session_state.theme)

    # Main Content - Switch based on view mode
    if st.session_state.view_mode == "dashboard":
        # Dashboard View
        st.title("📊 Learning Dashboard")
        st.markdown("### Track your progress and insights")
        st.markdown("---")
        
        db = TutorialDatabase()
        stats = db.get_study_statistics(st.session_state.session_id)
        
        # Summary Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📚 Total Lessons", stats['total_conversations'])
        with col2:
            st.metric("🎯 Subjects Studied", stats['unique_subjects'])
        with col3:
            st.metric("💬 Total Messages", stats['total_messages'])
        
        st.markdown("---")
        
        # Topic Breakdown Chart
        st.subheader("📈 Topics Overview")
        topics = db.get_topic_breakdown(st.session_state.session_id)
        
        if topics:
            # Create DataFrame for Altair
            topics_df = pd.DataFrame(topics)
            
            # Create bar chart
            chart = alt.Chart(topics_df).mark_bar().encode(
                x=alt.X('count:Q', title='Number of Lessons'),
                y=alt.Y('subject:N', title='Subject', sort='-x'),
                color=alt.Color('count:Q', scale=alt.Scale(scheme='blues'), legend=None),
                tooltip=['subject', 'count']
            ).properties(
                height=300
            )
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No learning data yet. Start a lesson to see your progress!")
        
        st.markdown("---")
        
        # Recent Activity
        st.subheader("📅 Recent Activity (Last 7 Days)")
        if stats['recent_activity']:
            activity_df = pd.DataFrame(stats['recent_activity'])
            
            activity_chart = alt.Chart(activity_df).mark_line(point=True).encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('count:Q', title='Lessons Started'),
                tooltip=['date', 'count']
            ).properties(
                height=200
            )
            
            st.altair_chart(activity_chart, use_container_width=True)
        else:
            st.info("No activity in the last 7 days")
        
        st.markdown("---")
        
        # Recent Lessons
        st.subheader("🕒 Recent Lessons")
        conversations = db.get_conversations_by_session(st.session_state.session_id)
        
        if conversations:
            for conv in conversations[:5]:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"**📝 {conv['subject']}**")
                    st.caption(f"Started: {conv['created_at']}")
                with col_b:
                    if st.button("Open", key=f"dash_open_{conv['id']}", use_container_width=True):
                        load_conversation(conv['id'])
                        switch_view_mode("chat")
                st.markdown("---")
        else:
            st.info("No lessons yet")
    
    elif st.session_state.current_conversation_id:
        # Chat View (existing code)
        # Header
        st.title(f"🎓 {st.session_state.subject}")
        st.markdown("---")
        
        # Chat History
        for idx, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    # Display image if present
                    if message.get("image_path"):
                        st.image(message["image_path"], width=300)
                    st.write(message["content"])
            else:
                with st.chat_message("assistant", avatar="🏛️"):
                    # Add icons based on message type
                    if message.get("type") == "tutorial":
                        st.markdown("### 📚 Lesson Content")
                    elif message.get("type") == "evaluation_question":
                        st.markdown("### 🤔 Quick Check")
                    elif message.get("type") == "evaluation_feedback":
                        st.markdown("### ✅ Feedback")
                    
                    st.write(message["content"])
                    
                    # Bookmark button for assistant messages (not in temporary mode)
                    if not str(st.session_state.current_conversation_id).startswith("temp_"):
                        bookmark_key = (st.session_state.current_conversation_id, idx)
                        is_bookmarked = bookmark_key in st.session_state.bookmarked_messages
                        
                        if st.button(
                            "★ Unbookmark" if is_bookmarked else "⭐ Bookmark",
                            key=f"bookmark_{idx}",
                            help="Save this message for later"
                        ):
                            toggle_bookmark(
                                st.session_state.current_conversation_id,
                                idx,
                                message["content"],
                                st.session_state.subject
                            )
                            st.rerun()

        
        # Quick Actions (Floating above chat input)
        st.markdown("###")  # Spacer
        cols = st.columns(4)
        actions = [
            ("📝 Examples", "Can you provide more examples?"),
            ("🔍 Deep Dive", "Can you explain this topic in more detail?"),
            ("🎯 Applications", "What are some real-world applications of this?"),
            ("🧠 Quiz Me", "Please test my understanding with a question.")
        ]
        
        for i, (label, prompt) in enumerate(actions):
            with cols[i]:
                if st.button(label, key=f"action_{i}", use_container_width=True):
                    handle_user_input(prompt)

        
        # Chat Input Area with Voice
        col1, col2 = st.columns([6, 1])
        
        with col1:
            if prompt := st.chat_input("Ask Socratic a question..."):
                handle_user_input(prompt)
        
        with col2:
            # Voice Input with improved styling
            st.markdown('<div class="mic-container">', unsafe_allow_html=True)
            audio = mic_recorder(
                start_prompt="🎤",
                stop_prompt="⏹️",
                key='recorder',
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

            
            # Fix microphone loop by tracking processed audio
            if audio and audio.get('bytes'):
                # Create a hash of the audio to track if we've processed it
                import hashlib
                audio_hash = hashlib.md5(audio['bytes']).hexdigest()
                
                # Only process if this is new audio (different from last processed)
                if st.session_state.audio_processed != audio_hash:
                    st.session_state.audio_processed = audio_hash
                    transcribed_text = transcribe_audio(audio['bytes'])
                    if transcribed_text:
                        handle_user_input(transcribed_text)
            
    else:
        # Welcome Screen
        st.title("🏛️ Socratic")
        st.markdown("### *Unlock your potential with AI-powered learning.*")
        
        theme_accent = THEMES[st.session_state.theme]["accent_color"]
        theme_bg = THEMES[st.session_state.theme]["chat_user_bg"]
        
        st.markdown(f"""
        <div style="background-color: {theme_bg}; padding: 25px; border-radius: 15px; margin-bottom: 30px; border-left: 5px solid {theme_accent};">
            <h4>Welcome to Socratic!</h4>
            <p>I am your personal AI tutor. I can create custom lessons, answer your questions, and quiz you on any topic.</p>
            <p><strong>Select a topic below or type your own in the sidebar to begin.</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 💡 Popular Topics")
        
        example_subjects = [
            "Python Programming", "Machine Learning", "Data Science",
            "Web Development", "Statistics", "Linear Algebra",
            "Computer Networks", "Database Design", "API Development"
        ]
        
        # Grid Layout for Topics
        cols = st.columns(3)
        for i, subject in enumerate(example_subjects):
            col_idx = i % 3
            with cols[col_idx]:
                if st.button(f"📚 {subject}", key=f"example_{i}", use_container_width=True):
                    start_new_tutorial(subject)

if __name__ == "__main__":
    main()