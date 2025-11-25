# 🤖 Socratic - AI Tutorial Agent

An interactive, intelligent tutoring system built with LangGraph and Streamlit that adapts to your learning style. Socratic helps you master any subject through structured tutorials, interactive Q&A, and personalized knowledge evaluation.

## 🌟 Features

### 🚀 Core Learning Experience
- **📚 Adaptive Tutorials**: Generates comprehensive, structured lessons on *any* topic you choose.
- **💬 Interactive Socratic Method**: Uses the Socratic method to guide you to answers rather than just giving them.
- **🧠 Knowledge Checks**: Periodically tests your understanding with quizzes and provides constructive feedback.
- **🗣️ Voice Interaction**: Speak your questions naturally using the built-in voice recorder.

### 🛠️ Productivity Tools
- **📊 Progress Dashboard**: Track your learning journey with detailed statistics and visualizations of topics studied.
- **📥 PDF Export**: Download your entire lesson history as a beautifully formatted PDF for offline study.
- **🔖 Smart Bookmarks**: Save important explanations or "aha!" moments for quick reference later.
- **🔍 Deep Search**: Instantly find past discussions across all your learning sessions.
- **🌗 Dark Mode**: Sleek "Midnight Pro" theme by default for comfortable late-night study sessions.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- An API Key from [OpenRouter](https://openrouter.ai/) (for LLM access)

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/shreyaspanda/Socratic.git
cd Socratic
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory (or set environment variables) with your API key:

```env
OPENROUTER_API_KEY=your_api_key_here
```

### 4. Run the Application

```bash
streamlit run streamlit_app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

## 📖 How to Use

1.  **Start a Lesson**: In the sidebar, type a topic (e.g., "Quantum Physics", "French Revolution") and click "Start Learning".
2.  **Interact**: Read the tutorial, then ask follow-up questions in the chat. You can type or use the **microphone button** 🎤 to speak.
3.  **Save & Organize**:
    *   Click **⭐ Bookmark** on any message to save it.
    *   Use the **Sidebar** to access Bookmarks, Search History, or start a New Chat.
4.  **Review**:
    *   Click **📊 Dashboard** to see your learning stats.
    *   Click **📥 Export PDF** to save the current lesson.

## 🏗️ Technical Architecture

- **Frontend**: [Streamlit](https://streamlit.io/) - For a responsive, interactive web UI.
- **Orchestration**: [LangGraph](https://langchain-ai.github.io/langgraph/) - Manages the complex state and flow of the tutoring agent.
- **Database**: SQLite - Robust local storage for conversations, bookmarks, and history.
- **AI Model**: Uses advanced LLMs via OpenRouter (e.g., Llama 3, GPT-4) for high-quality tutoring.
- **Voice**: `streamlit-mic-recorder` for audio capture and processing.
- **Analytics**: `Altair` for data visualization in the dashboard.

## 📂 Project Structure

```
AITutorAgent/
├── streamlit_app.py      # Main application entry point & UI logic
├── tutorial_agent.py     # LangGraph agent definition & core logic
├── database.py           # SQLite database management (History, Bookmarks)
├── pdf_export.py         # PDF generation utility
├── image_handler.py      # Image processing (Vision capabilities)
├── requirements.txt      # Project dependencies
└── README.md             # Documentation
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

