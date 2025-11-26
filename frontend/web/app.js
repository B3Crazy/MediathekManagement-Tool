// Backend API URL
const API_URL = 'http://localhost:8000';

// State
let videoUrls = [];
let audioUrls = [];
let currentVideoTaskId = null;
let currentAudioTaskId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkBackendStatus();
    setInterval(checkBackendStatus, 10000); // Check every 10 seconds
    
    // Enable enter key for URL inputs
    document.getElementById('video-url-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addVideoUrl();
    });
    document.getElementById('audio-url-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addAudioUrl();
    });
});

// Tab switching
function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tab}-tab`).classList.add('active');
}

// Backend status check
async function checkBackendStatus() {
    try {
        const response = await fetch(`${API_URL}/health`, { method: 'GET' });
        const statusEl = document.getElementById('backend-status');
        const indicatorEl = document.getElementById('backend-indicator');
        
        if (response.ok) {
            statusEl.classList.add('online');
            statusEl.classList.remove('offline');
            indicatorEl.textContent = 'Online ✓';
        } else {
            throw new Error('Backend not healthy');
        }
    } catch (error) {
        const statusEl = document.getElementById('backend-status');
        const indicatorEl = document.getElementById('backend-indicator');
        statusEl.classList.add('offline');
        statusEl.classList.remove('online');
        indicatorEl.textContent = 'Offline ✗';
    }
}

// Video URL management
function addVideoUrl() {
    const input = document.getElementById('video-url-input');
    const url = input.value.trim();
    
    if (!url) {
        alert('Bitte geben Sie eine URL ein.');
        return;
    }
    
    if (!isValidYoutubeUrl(url)) {
        alert('Bitte geben Sie eine gültige YouTube-URL ein.');
        return;
    }
    
    if (videoUrls.includes(url)) {
        alert('Diese URL ist bereits in der Liste.');
        return;
    }
    
    videoUrls.push(url);
    updateVideoUrlList();
    input.value = '';
}

function removeVideoUrl(index) {
    videoUrls.splice(index, 1);
    updateVideoUrlList();
}

function clearVideoUrls() {
    if (videoUrls.length === 0) return;
    if (confirm('Möchten Sie alle URLs aus der Liste entfernen?')) {
        videoUrls = [];
        updateVideoUrlList();
    }
}

function updateVideoUrlList() {
    const list = document.getElementById('video-url-list');
    list.innerHTML = '';
    
    if (videoUrls.length === 0) {
        list.innerHTML = '<li style="text-align: center; color: #999;">Keine URLs hinzugefügt</li>';
        return;
    }
    
    videoUrls.forEach((url, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${url}</span>
            <button onclick="removeVideoUrl(${index})">Entfernen</button>
        `;
        list.appendChild(li);
    });
}

// Audio URL management
function addAudioUrl() {
    const input = document.getElementById('audio-url-input');
    const url = input.value.trim();
    
    if (!url) {
        alert('Bitte geben Sie eine URL ein.');
        return;
    }
    
    if (!isValidYoutubeUrl(url)) {
        alert('Bitte geben Sie eine gültige YouTube-URL ein.');
        return;
    }
    
    if (audioUrls.includes(url)) {
        alert('Diese URL ist bereits in der Liste.');
        return;
    }
    
    audioUrls.push(url);
    updateAudioUrlList();
    input.value = '';
}

function removeAudioUrl(index) {
    audioUrls.splice(index, 1);
    updateAudioUrlList();
}

function clearAudioUrls() {
    if (audioUrls.length === 0) return;
    if (confirm('Möchten Sie alle URLs aus der Liste entfernen?')) {
        audioUrls = [];
        updateAudioUrlList();
    }
}

function updateAudioUrlList() {
    const list = document.getElementById('audio-url-list');
    list.innerHTML = '';
    
    if (audioUrls.length === 0) {
        list.innerHTML = '<li style="text-align: center; color: #999;">Keine URLs hinzugefügt</li>';
        return;
    }
    
    audioUrls.forEach((url, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${url}</span>
            <button onclick="removeAudioUrl(${index})">Entfernen</button>
        `;
        list.appendChild(li);
    });
}

// URL validation
function isValidYoutubeUrl(url) {
    return url.startsWith('https://www.youtube.com/') || 
           url.startsWith('https://youtu.be/') || 
           url.startsWith('https://m.youtube.com/');
}

// Video download
async function startVideoDownload() {
    if (videoUrls.length === 0) {
        alert('Bitte fügen Sie mindestens eine URL hinzu.');
        return;
    }
    
    const format = document.querySelector('input[name="video-format"]:checked').value;
    const path = document.getElementById('video-path').value.trim();
    
    if (!path) {
        alert('Bitte geben Sie einen Speicherort an.');
        return;
    }
    
    const button = document.getElementById('video-download-btn');
    button.disabled = true;
    button.textContent = 'Download läuft...';
    
    try {
        const response = await fetch(`${API_URL}/api/download/video`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                urls: videoUrls,
                format: format,
                output_path: path
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download fehlgeschlagen');
        }
        
        const result = await response.json();
        currentVideoTaskId = result.task_id;
        updateVideoStatus('Download gestartet...');
        pollVideoStatus();
        
    } catch (error) {
        alert(`Fehler: ${error.message}`);
        button.disabled = false;
        button.textContent = 'Download starten';
    }
}

function pollVideoStatus() {
    if (!currentVideoTaskId) return;
    
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_URL}/api/status/${currentVideoTaskId}`);
            if (!response.ok) throw new Error('Status abrufen fehlgeschlagen');
            
            const status = await response.json();
            updateVideoProgress(status.progress);
            updateVideoStatus(status.message);
            
            if (status.status === 'complete') {
                clearInterval(interval);
                const button = document.getElementById('video-download-btn');
                button.disabled = false;
                button.textContent = 'Download starten';
                currentVideoTaskId = null;
                
                alert(`Download abgeschlossen!\nFehlgeschlagen: ${status.failed_urls.length}`);
            }
        } catch (error) {
            console.error('Error polling status:', error);
        }
    }, 1000);
}

function updateVideoProgress(progress) {
    const fill = document.querySelector('#video-progress-bar .progress-fill');
    fill.style.width = `${progress}%`;
    fill.textContent = `${Math.round(progress)}%`;
}

function updateVideoStatus(message) {
    document.getElementById('video-status').textContent = message;
}

// Audio download
async function startAudioDownload() {
    if (audioUrls.length === 0) {
        alert('Bitte fügen Sie mindestens eine URL hinzu.');
        return;
    }
    
    const format = document.querySelector('input[name="audio-format"]:checked').value;
    const path = document.getElementById('audio-path').value.trim();
    
    if (!path) {
        alert('Bitte geben Sie einen Speicherort an.');
        return;
    }
    
    const button = document.getElementById('audio-download-btn');
    button.disabled = true;
    button.textContent = 'Download läuft...';
    
    try {
        const response = await fetch(`${API_URL}/api/download/audio`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                urls: audioUrls,
                format: format,
                output_path: path
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download fehlgeschlagen');
        }
        
        const result = await response.json();
        currentAudioTaskId = result.task_id;
        updateAudioStatus('Download gestartet...');
        pollAudioStatus();
        
    } catch (error) {
        alert(`Fehler: ${error.message}`);
        button.disabled = false;
        button.textContent = 'Download starten';
    }
}

function pollAudioStatus() {
    if (!currentAudioTaskId) return;
    
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_URL}/api/status/${currentAudioTaskId}`);
            if (!response.ok) throw new Error('Status abrufen fehlgeschlagen');
            
            const status = await response.json();
            updateAudioProgress(status.progress);
            updateAudioStatus(status.message);
            
            if (status.status === 'complete') {
                clearInterval(interval);
                const button = document.getElementById('audio-download-btn');
                button.disabled = false;
                button.textContent = 'Download starten';
                currentAudioTaskId = null;
                
                alert(`Download abgeschlossen!\nFehlgeschlagen: ${status.failed_urls.length}`);
            }
        } catch (error) {
            console.error('Error polling status:', error);
        }
    }, 1000);
}

function updateAudioProgress(progress) {
    const fill = document.querySelector('#audio-progress-bar .progress-fill');
    fill.style.width = `${progress}%`;
    fill.textContent = `${Math.round(progress)}%`;
}

function updateAudioStatus(message) {
    document.getElementById('audio-status').textContent = message;
}
