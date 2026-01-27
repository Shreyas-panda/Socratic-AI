# 🤖 Socratic - AI Tutorial Agent

An interactive, intelligent tutoring system built with **Flask**, **LangGraph**, and a custom **HTML/CSS/JS** frontend. Socratic helps you master any subject through structured tutorials, interactive Q&A, and personalized knowledge evaluation.

## 🌟 Features

### 🚀 Core Learning Experience
- **📚 Adaptive Tutorials**: Generates comprehensive, structured lessons on *any* topic you choose.
- **💬 Interactive Socratic Method**: Uses the Socratic method to guide you to answers rather than just giving them.
- **🧠 Knowledge Checks**: Periodically tests your understanding with quizzes and provides constructive feedback.
- **🗣️ Voice Interaction**: Speak your questions naturally using the built-in voice recorder (Speech-to-Text).
- **🔊 Text-to-Speech**: Listen to AI responses with built-in TTS - click the volume button on any message.
- **📷 Image Analysis**: Upload diagrams or text snippets (including HEIC format), and the AI will analyze and explain them.
- **📄 Document Upload (RAG)**: Upload PDF, TXT, or Markdown files to build a personal knowledge base. The AI will reference your documents when answering questions.

### ⚡ Performance & Speed
- **🚀 Streaming Responses**: See AI responses appear in real-time as they're generated.
- **🔄 Multiple Model Support**: Uses Groq API (Llama 3.3 70B) for blazing fast inference with fallback to OpenRouter.
- **⏹️ Stop Generation**: Stop long responses at any time with the stop button.

### 🛠️ Productivity Tools
- **📊 Progress Dashboard**: Track your learning journey with detailed statistics and visualizations.
- **📥 PDF Export**: Download your entire lesson history as a beautifully formatted PDF.
- **🗑️ Knowledge Base Management**: Clear and rebuild your document knowledge base anytime.
- **🌗 Dark Mode**: Sleek "Midnight Pro" theme by default for comfortable late-night study sessions.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- An API Key from [Groq](https://console.groq.com/) (recommended - fast & free) or [OpenRouter](https://openrouter.ai/)

### 2. Installation

```bash
git clone https://github.com/Shreyas-panda/Socratic-AI.git
cd Socratic-AI

# Create a virtual environment (Recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory with your API keys:

```env
FLASK_SECRET_KEY=your_secret_key
GROQ_API_KEY=gsk_your_groq_key_here          # Recommended - fast & free
OPENROUTER_API_KEY=your_openrouter_key       # Optional fallback
```

> **Note**: Groq offers 14,400 free requests/day with lightning-fast inference. OpenRouter's free tier is limited to 50 requests/day.

### 4. Run the Application

```bash
python3 app.py
```

The app will be available at `http://127.0.0.1:5001`.

## 📖 How to Use

1. **Start a Lesson**: Type a topic (e.g., "Quantum Physics", "Machine Learning") and click start.
2. **Upload Documents**: Click the 📄 button to upload PDFs or text files for the AI to reference.
3. **Ask Questions**: Type or use the 🎤 microphone button to speak your questions.
4. **Listen to Responses**: Click the 🔊 button on any AI message to hear it read aloud.
5. **Stop Generation**: Click ⏹️ to stop a long response.
6. **Clear Knowledge Base**: Click 🗑️ to remove all uploaded documents and start fresh.

## 🏗️ Technical Architecture

| Component | Technology |
|-----------|------------|
| **Backend** | Flask + Python 3.8+ |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **AI Orchestration** | LangGraph (state machine) |
| **LLM API** | Groq (primary) / OpenRouter (fallback) |
| **RAG** | FAISS + HuggingFace Embeddings |
| **Database** | SQLite |
| **Voice** | Web Speech API + SpeechRecognition |

## 📂 Project Structure

```
Socratic-AI/
├── app.py                 # Main Flask application
├── tutorial_agent.py      # LangGraph agent logic
├── LLM_api.py             # LLM client configuration
├── database.py            # SQLite database
├── image_handler.py       # Image upload & analysis
├── rag_engine.py          # RAG facade (modular architecture)
├── rag_loader.py          # Document loading
├── rag_embeddings.py      # Embedding model
├── rag_vectorstore.py     # FAISS vector store
├── rag_retriever.py       # Context retrieval
├── templates/             # HTML templates
│   ├── layout.html
│   ├── chat.html
│   └── dashboard.html
├── static/
│   ├── css/style.css      # Modern UI styles
│   └── js/
│       ├── main.js        # Core frontend logic
│       └── recorder.js    # Audio recording
├── requirements.txt
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).
