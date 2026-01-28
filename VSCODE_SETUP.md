# Socratic AI - VS Code Setup Guide

To continue working on **Socratic AI** in VS Code, follow these steps:

## 1. Open the Project in VS Code
Since the project is already located on your desktop, you can open it directly:
- Open **VS Code**.
- Go to `File` -> `Open Folder...`
- Navigate to `/Users/shreyaspanda/Desktop/Socratic-AI` and click **Open**.
- **Alternative (Terminal):** Open your terminal and type:
  ```bash
  code /Users/shreyaspanda/Desktop/Socratic-AI
  ```

## 2. Set Up Your Environment
It's best to use a virtual environment to manage dependencies.
- Open the integrated terminal in VS Code (`Ctrl + ` ` or `View` -> `Terminal`).
- Create and activate a virtual environment:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- Install the required packages:
  ```bash
  pip install -r requirements.txt
  ```

## 3. Configure API Keys
Ensure your `.env` file is present in the root directory with your keys:
```env
GROQ_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

## 4. Run the Application
You can run the Flask server directly from the VS Code terminal:
```bash
python3 app.py
```
Then visit `http://127.0.0.1:5001` in your browser.

## 5. Recommended Extensions
For the best experience, install these VS Code extensions:
- **Python** (by Microsoft)
- **HTML CSS Support**
- **ESLint** (for Javascript)
- **SQLite Viewer** (to inspect `tutorial_app.db`)

---
**Happy Coding!** 🚀
