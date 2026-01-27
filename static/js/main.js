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

    // Mobile: Close sidebar when clicking a nav item (if on mobile)
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                toggleSidebar();
            }
        });
    });

    // Initialize Sidebar Resizer
    initSidebarResizer();
});

function initSidebarResizer() {
    const resizer = document.querySelector('.resizer');
    const sidebar = document.querySelector('.sidebar');
    const root = document.documentElement;
    let isResizing = false;

    if (!resizer) return;

    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        sidebar.style.transition = 'none'; // Disable transition during drag
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        // Calculate new width
        let newWidth = e.clientX;

        // Min/Max constraints
        if (newWidth < 200) newWidth = 200;
        if (newWidth > 500) newWidth = 500;

        root.style.setProperty('--sidebar-width', `${newWidth}px`);
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = 'default';
            sidebar.style.transition = ''; // Re-enable transition
        }
    });
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('active');
}

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

    // Validate size (e.g., 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert("File is too large. Max size is 5MB.");
        input.value = '';
        return;
    }

    // Set global file variable
    window.selectedImageFile = file;

    // Show Preview
    const reader = new FileReader();
    reader.onload = function (e) {
        const previewImg = document.getElementById('preview-img');
        const previewName = document.getElementById('preview-filename');
        const previewContainer = document.getElementById('image-preview');

        if (previewImg && previewContainer) {
            previewImg.src = e.target.result;
            if (previewName) previewName.innerText = file.name;
            previewContainer.style.display = 'flex';
        }
    };
    reader.readAsDataURL(file);

    // Reset input value so same file can be selected again if cleared
    input.value = '';
}

function clearImage() {
    window.selectedImageFile = null;
    const previewContainer = document.getElementById('image-preview');
    if (previewContainer) {
        previewContainer.style.display = 'none';
        document.getElementById('preview-img').src = '';
    }
}

async function handleDocumentUpload(input) {
    const file = input.files[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
        alert("File is too large. Max size is 10MB.");
        input.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('document', file);

    const btn = document.getElementById('doc-upload-btn');
    // Guard against null button
    if (!btn) {
        console.error("Upload button not found!");
        // Continue anyway to try upload, but skip UI spin
    }

    let originalIcon = '';
    if (btn) {
        originalIcon = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        btn.disabled = true;
    }

    try {
        console.log("Starting upload...");
        const response = await fetch('/api/upload_document', {
            method: 'POST',
            body: formData
        });

        console.log("Upload status:", response.status);
        const data = await response.json();
        console.log("Upload response:", data);

        if (data.status === 'success') {
            const successMsg = `Document uploaded successfully: ${data.message}`;
            console.log(successMsg);
            alert(successMsg);
            // Optionally show it in UI
            if (typeof appendMessage === 'function') {
                appendMessage('assistant', `_I have read **${data.filename}**. You can now ask me questions about it._`);
            }
        } else {
            console.error("Server returned error:", data.error);
            alert('Upload failed: ' + (data.error || 'Unknown server error'));
        }
    } catch (error) {
        console.error('Frontend Upload Error:', error);
        alert('Failed to upload document. See console for details.');
    } finally {
        if (btn) {
            btn.innerHTML = originalIcon;
            btn.disabled = false;
        }
        input.value = '';
    }
}

async function clearKnowledgeBase() {
    if (!confirm('This will remove all uploaded documents from the knowledge base. Continue?')) {
        return;
    }

    const btn = document.getElementById('clear-kb-btn');
    const originalIcon = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;

    try {
        const response = await fetch('/api/clear_knowledge_base', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('✓ ' + data.message);
        } else {
            alert('Failed: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Clear KB Error:', error);
        alert('Failed to clear knowledge base.');
    } finally {
        btn.innerHTML = originalIcon;
        btn.disabled = false;
    }
}
