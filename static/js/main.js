document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggling
    const themeToggleBtn = document.getElementById('theme-toggle');
    const body = document.body;

    // Check local storage for preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        body.className = savedTheme;
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            if (body.classList.contains('theme-midnight')) {
                body.classList.remove('theme-midnight');
                body.classList.add('theme-nordic');
                localStorage.setItem('theme', 'theme-nordic');
            } else {
                body.classList.remove('theme-nordic');
                body.classList.add('theme-midnight');
                localStorage.setItem('theme', 'theme-midnight');
            }
        });
    }

    // Auto-resize textarea
    const autoResizeTextarea = (element) => {
        element.style.height = 'auto';
        element.style.height = element.scrollHeight + 'px';
    };

    const chatInputs = document.querySelectorAll('textarea.chat-input');
    chatInputs.forEach(textarea => {
        textarea.addEventListener('input', () => autoResizeTextarea(textarea));
    });

    // Load History
    loadSidebarHistory();
});

async function loadSidebarHistory() {
    const listContainer = document.getElementById('history-list');
    if (!listContainer) return;

    try {
        const response = await fetch('/api/history');
        const conversations = await response.json();

        listContainer.innerHTML = '';

        if (conversations.length === 0) {
            listContainer.innerHTML = '<div style="padding: 1rem; color: var(--text-secondary); font-size: 0.8rem; font-style: italic;">No recent lessons</div>';
            return;
        }

        conversations.slice(0, 10).forEach(conv => {
            const a = document.createElement('a');
            a.href = `/load_chat/${conv.id}`;
            a.className = 'nav-item';
            a.style.fontSize = '0.9rem';
            a.innerHTML = `<i class="fas fa-history" style="font-size: 0.8em; opacity: 0.7;"></i> ${conv.subject}`;
            listContainer.appendChild(a);
        });
    } catch (e) {
        console.error("Failed to load history", e);
    }
}

async function clearHistory() {
    if (!confirm('Are you sure you want to clear your learning history?')) return;

    try {
        await fetch('/api/history', { method: 'DELETE' });
        loadSidebarHistory(); // Refresh list
    } catch (e) {
        console.error("Failed to clear history", e);
    }
}

async function toggleTempMode(checkbox) {
    try {
        await fetch('/toggle_temp_mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: checkbox.checked })
        });
    } catch (e) {
        console.error(e);
    }
}
