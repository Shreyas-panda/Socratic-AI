# Feature Implementation: Interactive & Auth

## Goal
Implement the user's requested features:
1.  **Stop Generation**: Allow cancelling the AI request.
2.  **Copy Code**: Verify and polish the code copy functionality.
3.  **TTS**: Text-To-Speech for AI responses.
4.  **User Authentication**: Email/Password login for persistent history.

## Proposed Changes

---

### 1. Interactive Features (Frontend Only)

#### Stop Generation
- **Target**: `templates/chat.html`, `static/js/main.js`
- **Logic**: 
    - Add an `AbortController` to the `fetch` request in `sendMessage`.
    - Provide a "Stop" button that triggers `controller.abort()`.
    - Handle the `AbortError` gracefully in the UI.

#### Text-to-Speech (TTS)
- **Target**: `templates/chat.html`, `static/js/main.js`
- **Logic**:
    - Use Web Speech API (`window.speechSynthesis`) for immediate, client-side TTS (supports multiple languages).
    - Add a "Speaker" icon next to AI messages.
    - Toggle functionality (Play/Stop).

#### Copy Button
- **Verification**: Check if existing implementation works. If so, ensure styles are visible and button feedback is clear.

---

### 2. User Authentication (Backend & DB)

#### Database Schema
- **Target**: `database.py`
- **Changes**:
    - Add `users` table: `id`, `email`, `password_hash`, `created_at`.
    - Update `conversations` table to link to `user_id` (already doing this loosely, but need to enforce FK).

#### Authentication Routes
- **Target**: `app.py`
- **Changes**:
    - Add `/login`, `/register`, `/logout` routes.
    - Use `werkzeug.security` for hashing.
    - Update `load_user` logic to check session for logged-in user, else fallback to guest or redirect.

#### Frontend Maps
- **Target**: `templates/login.html` (New), `templates/register.html` (New).
- **Update**: `layout.html` to show Login/Signup vs Logout/Profile.
- **Update**: Sidebar to show "Guest" vs "User Name".

## Verification Plan

### Interactive
- [ ] Start a long query. Click "Stop". Verify loading stops and UI returns to ready state.
- [ ] Click "Speak" on an AI message. Verify audio plays. Click again to stop.
- [ ] Check code blocks. Click "Copy". Paste to notepad to verify.

### Auth
- [ ] Register a new account `test@example.com`.
- [ ] Log out. Log in.
- [ ] Create a chat. Log out. Log back in. Verify chat history persists.
- [ ] Open incognito window. Log in. Verify history appears.
