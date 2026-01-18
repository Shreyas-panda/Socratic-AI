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

async function exportPDF() {
    const btn = document.querySelector('button[onclick="exportPDF()"]');
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/export_pdf');

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'Socratic_Lesson.pdf';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch.length === 2)
                    filename = filenameMatch[1];
            }

            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            const data = await response.json();
            alert('Export failed: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('PDF Export Error:', error);
        alert('Failed to export PDF');
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

async function handleImageUpload(input) {
    const file = input.files[0];
    if (!file) return;

    const originalIcon = input.nextElementSibling.innerHTML;
    input.nextElementSibling.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    input.nextElementSibling.disabled = true;

    const formData = new FormData();
    formData.append('image', file);
    formData.append('question', "Explain this image to me.");

    try {
        const response = await fetch('/api/upload_image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            window.location.reload();
        } else {
            alert('Upload failed: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        console.error('Image upload failed', e);
        alert('Failed to upload image');
    } finally {
        input.nextElementSibling.innerHTML = originalIcon;
        input.nextElementSibling.disabled = false;
        input.value = '';
    }
}
