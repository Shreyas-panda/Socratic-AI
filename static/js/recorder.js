// recorder.js
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

document.addEventListener('DOMContentLoaded', () => {
    const micBtn = document.getElementById('mic-btn');
    if (!micBtn) return;

    micBtn.addEventListener('click', async () => {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Check for supported mime types
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : 'audio/webm';

            mediaRecorder = new MediaRecorder(stream, { mimeType });
            audioChunks = [];

            mediaRecorder.addEventListener('dataavailable', event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            });

            mediaRecorder.addEventListener('stop', () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' }); // Chrome uses webm
                sendAudio(audioBlob);
            });

            mediaRecorder.start();
            isRecording = true;
            micBtn.classList.add('recording');
            micBtn.innerHTML = '<i class="fas fa-stop"></i>';
        } catch (err) {
            console.error('Error accessing microphone:', err);
            alert('Could not access microphone');
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            isRecording = false;
            micBtn.classList.remove('recording');
            micBtn.innerHTML = '<i class="fas fa-microphone"></i>';

            // Stop all tracks
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }

    async function sendAudio(blob) {
        const formData = new FormData();
        formData.append('audio', blob, 'recording.webm');

        const messageInput = document.getElementById('message-input');
        // If message input doesn't exist (e.g. start screen), try subject input
        const subjectInput = document.getElementById('subject-input');
        const activeInput = messageInput || subjectInput;

        if (activeInput) {
            activeInput.placeholder = "Processing audio...";
            activeInput.disabled = true;
        }

        try {
            const response = await fetch('/api/audio', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.text) {
                // Populate input box
                if (activeInput) {
                    activeInput.value = data.text;
                    activeInput.focus();

                    // Auto-send if it's the chat message input
                    if (activeInput.id === 'message-input') {
                        const sendBtn = document.getElementById('send-btn');
                        if (sendBtn) sendBtn.click();
                    }

                    if (activeInput.tagName === 'TEXTAREA') {
                        activeInput.style.height = 'auto';
                        activeInput.style.height = activeInput.scrollHeight + 'px';
                    }
                }
            } else if (data.error) {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error sending audio:', error);
            alert('Error processing audio. Please try again.');
        } finally {
            if (activeInput) {
                activeInput.placeholder = activeInput.id === 'subject-input' ? "What sparks your curiosity today?" : "Ask a follow-up question...";
                activeInput.disabled = false;
            }
        }
    }

    // Helper needed here too since it's a separate file or script block
    function appendMessage(role, text) {
        const chatHistory = document.getElementById('chat-history');
        if (!chatHistory) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = text;

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(content);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});
