# 🤖 Socratic - AI Tutorial Agent

An interactive, intelligent tutoring system built with **Flask**, **LangGraph**, and a custom **HTML/CSS/JS** frontend. Socratic helps you master any subject through structured tutorials, interactive Q&A, and personalized knowledge evaluation.

## 🌟 Features

### 🚀 Core Learning Experience
- **📚 Adaptive Tutorials**: Generates comprehensive, structured lessons on *any* topic you choose.
- **💬 Interactive Socratic Method**: Uses the Socratic method to guide you to answers rather than just giving them.
- **🧠 Knowledge Checks**: Periodically tests your understanding with quizzes and provides constructive feedback.
- **🗣️ Voice Interaction**: Speak your questions naturally using the built-in voice recorder (Speech-to-Text).
- **📷 Image Analysis**: Upload diagrams or text snippets, and the AI will analyze and explain them to you.

### 🛠️ Productivity Tools
- **📊 Progress Dashboard**: Track your learning journey with detailed statistics and visualizations of topics studied.
- **📥 PDF Export**: Download your entire lesson history as a beautifully formatted PDF for offline study
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
# Create a virtual environment (Recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory (or set environment variables) with your API key:

```env
FLASK_SECRET_KEY=your_secret_key
OPENROUTER_API_KEY=your_api_key_here
```

### 4. Run the Application

```bash
python3 app.py
```

The app will open automatically in your browser at `http://127.0.0.1:5000`.

## 📖 How to Use

1.  **Start a Lesson**: In the main menu, type a topic (e.g., "Quantum Physics", "French Revolution") and click the arrow button.
2.  **Interact**: Read the tutorial, then ask follow-up questions in the chat. You can type, use the **microphone button** 🎤 to speak, or **upload images** 📷 for analysis.
3.  **Save & Organize**:
    *   Use the **Sidebar** to access History, Start a New Chat, or View the Dashboard.
4.  **Review**:
    *   Click **📊 Dashboard** to see your learning stats.

## 🏗️ Technical Architecture

- **Backend**: [Flask](https://flask.palletsprojects.com/) - Proper web server handling API routes and session management.
- **Frontend**: HTML5, CSS3, Vanilla JavaScript - For a fully custom, responsive, and high-performance UI.
- **Orchestration**: [LangGraph](https://langchain-ai.github.io/langgraph/) - Manages the complex state and flow of the tutoring agent.
- **Database**: SQLite - Robust local storage for conversations, bookmarks, and history.
- **AI Model**: Uses advanced LLMs via OpenRouter (e.g., Llama 3, GPT-4) for high-quality tutoring.
- **Voice**: Native `MediaRecorder` API + Server-side `pydub`/`SpeechRecognition` for audio processing.

## 📂 Project Structure

```
Socratic/
├── app.py                # Main Flask application entry point
├── database.py           # SQLite database management
├── tutorial_agent.py     # LangGraph agent definition & core logic
├── templates/            # HTML Templates
│   ├── layout.html       # Base layout with sidebar
│   ├── chat.html         # Main Chat Interface
│   └── dashboard.html    # Analytics Dashboard
├── static/               # Static Assets
│   ├── css/              # Stylesheets
│   │   └── style.css     # Main CSS
│   └── js/               # JavaScript
│       ├── main.js       # Core frontend logic
│       └── recorder.js   # Audio recording logic
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

