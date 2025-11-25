# 🚀 GitHub & Deployment Guide

This guide covers how to upload your **Socratic AI Tutor** to GitHub and deploy it live on the web using Streamlit Community Cloud.

---

## Part 1: Push to GitHub

### 1. Initialize Git (if not already done)
Open your terminal in the project folder (`AITutorAgent`) and run:

```bash
git init
```

### 2. Create a `.gitignore` file
It's crucial to ignore sensitive files (like your API keys) and unnecessary system files. Create a file named `.gitignore` and add:

```text
.env
__pycache__/
*.pyc
.DS_Store
venv/
tutorial_agent.db
uploaded_images/
```

### 3. Commit Your Code
Stage and commit all your files:

```bash
git add .
git commit -m "Initial commit: Socratic AI Tutor with all features"
```

### 4. Create a Repository on GitHub
1.  Go to [GitHub.com](https://github.com) and log in.
2.  Click the **+** icon in the top right -> **New repository**.
3.  Name it `Socratic` (or whatever you prefer).
4.  Make it **Public** (required for free Streamlit deployment) or Private.
5.  Do **not** initialize with README/gitignore (we already have them).
6.  Click **Create repository**.

### 5. Push Code
Copy the commands shown on GitHub under "…or push an existing repository from the command line" and run them. They will look like this:

```bash
git remote add origin https://github.com/YOUR_USERNAME/Socratic.git
git branch -M main
git push -u origin main
```

---

## Part 2: Deploy to Streamlit Community Cloud

Streamlit Community Cloud is the easiest and free way to deploy Streamlit apps directly from GitHub.

### 1. Sign Up / Log In
Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.

### 2. Create New App
1.  Click **"New app"** (top right).
2.  **Repository**: Select your `AITutorAgent` repo from the dropdown.
3.  **Branch**: `main`.
4.  **Main file path**: `streamlit_app.py`.
5.  **App URL**: You can customize the subdomain (e.g., `socratic-tutor.streamlit.app`).

### 3. Configure Secrets (Crucial!)
Since we didn't upload our `.env` file (for security), we need to give the cloud server our API key.

1.  Click **"Advanced settings"**.
2.  In the **"Secrets"** box, enter your API key like this:

```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
```

3.  Click **Save**.

### 4. Deploy!
Click **"Deploy!"**.

Streamlit will now build your app. It will install all packages from `requirements.txt` and launch the app. This usually takes 1-2 minutes.

---

## 🎉 Done!
Your app is now live! You can share the link with anyone.

### Troubleshooting Deployment
- **"ModuleNotFoundError"**: Ensure the missing package is listed in `requirements.txt`.
- **"KeyError: OPENROUTER_API_KEY"**: You forgot to set the Secret in Step 3.
- **Database Errors**: The app uses SQLite. On Streamlit Cloud, the database is ephemeral (it resets when the app restarts). For persistent storage in production, you would typically connect to a cloud database (like Supabase or Google Sheets), but for a demo/portfolio project, the ephemeral SQLite is fine (just know that history clears on reboot).
