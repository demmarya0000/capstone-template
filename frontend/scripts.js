const API_URL = 'http://localhost:8000';

const micBtn = document.getElementById('micBtn');
const statusText = document.getElementById('statusText');
const waveAnimation = document.getElementById('waveAnimation');
const messages = document.getElementById('messages');
const welcomeScreen = document.getElementById('welcomeScreen');
const newChatBtn = document.getElementById('newChatBtn');
const connectionStatus = document.getElementById('connectionStatus');

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let isProcessing = false;

micBtn.addEventListener('click', toggleRecording);
newChatBtn.addEventListener('click', startNewChat);

async function toggleRecording() {
    if (isProcessing) return;

    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await processAudio(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;
        
        micBtn.classList.add('recording');
        waveAnimation.classList.add('active');
        statusText.textContent = 'Listening... Click to stop';
        
        if (welcomeScreen.style.display !== 'none') {
            welcomeScreen.style.display = 'none';
        }
    } catch (error) {
        console.error('Error accessing microphone:', error);
        statusText.textContent = 'Microphone access denied';
        showNotification('Please allow microphone access', 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        isRecording = false;
        
        micBtn.classList.remove('recording');
        micBtn.classList.add('processing');
        waveAnimation.classList.remove('active');
        statusText.textContent = 'Processing...';
    }
}

async function processAudio(audioBlob) {
    isProcessing = true;

    try {
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        
        reader.onloadend = async () => {
            const base64Audio = reader.result.split(',')[1];
            
            const response = await fetch(`${API_URL}/api/process-audio`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ audio: base64Audio })
            });

            if (!response.ok) {
                throw new Error('Failed to process audio');
            }

            const data = await response.json();
            
            addMessage(data.transcription, 'user');
            
            setTimeout(() => {
                addMessage(data.response, 'assistant');
            }, 300);
            
            if (data.url) {
                setTimeout(() => {
                    window.open(data.url, '_blank');
                }, 500);
            }
            
            if (data.audio) {
                setTimeout(() => {
                    playAudio(data.audio);
                }, 600);
            }

            micBtn.classList.remove('processing');
            statusText.textContent = 'Click to speak';
            isProcessing = false;
        };
    } catch (error) {
        console.error('Error processing audio:', error);
        statusText.textContent = 'Error - Click to try again';
        addMessage('Sorry, there was an error processing your request. Please try again.', 'assistant');
        micBtn.classList.remove('processing');
        isProcessing = false;
    }
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;
    
    content.appendChild(messageText);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

function playAudio(base64Audio) {
    try {
        const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
        audio.play().catch(err => {
            console.error('Error playing audio:', err);
        });
    } catch (error) {
        console.error('Error creating audio:', error);
    }
}

function startNewChat() {
    messages.innerHTML = '';
    welcomeScreen.style.display = 'flex';
    showNotification('New chat started', 'success');
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'error' ? 'rgba(239, 68, 68, 0.9)' : 'rgba(74, 222, 128, 0.9)'};
        color: white;
        border-radius: 12px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_URL}/api/health`);
        if (response.ok) {
            connectionStatus.textContent = 'Connected';
            connectionStatus.style.color = '#4ade80';
            console.log('Backend is running');
        }
    } catch (error) {
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.style.color = '#ef4444';
        console.error('Backend is not running');
        showNotification('Backend server not connected', 'error');
    }
}

checkBackendHealth();
setInterval(checkBackendHealth, 30000);