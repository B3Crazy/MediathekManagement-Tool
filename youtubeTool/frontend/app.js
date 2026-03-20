// Backend API URL - automatically detect based on current host
function getApiUrl() {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // If accessing via localhost or 127.0.0.1, use localhost for backend
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    
    // Otherwise, use the same hostname with port 8000
    return `${protocol}//${hostname}:8000`;
}

const API_URL = getApiUrl();
console.log('Backend API URL:', API_URL);

// State
let videoUrls = [];
let audioUrls = [];
let currentVideoTaskId = null;
let currentAudioTaskId = null;
let videoFolderHandle = null;
let audioFolderHandle = null;

// Get user's home directory Downloads folder as default
const getDefaultDownloadPath = () => {
    return 'Downloads';
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    checkBackendStatus();
    setInterval(checkBackendStatus, 10000); // Check every 10 seconds
    
    // Enable enter key for URL inputs
    document.getElementById('video-url-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addVideoUrl();
    });
    document.getElementById('audio-url-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addAudioUrl();
    });
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchYoutube();
    });
});

// ============================================
// THEME MANAGEMENT
// ============================================

function initializeTheme() {
    // Check if user has a saved theme preference
    const savedTheme = localStorage.getItem('selectedTheme') || 'pride';
    
    // Detect system color scheme preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const mode = prefersDark ? 'dark' : 'light';
    
    // Apply theme
    applyTheme(savedTheme, mode);
    
    // Set dropdown value
    document.getElementById('theme-select').value = savedTheme;
    
    // Listen for system color scheme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        const currentTheme = localStorage.getItem('selectedTheme') || 'pride';
        const newMode = e.matches ? 'dark' : 'light';
        applyTheme(currentTheme, newMode);
    });
}

function changeTheme() {
    const theme = document.getElementById('theme-select').value;
    
    // Save preference
    localStorage.setItem('selectedTheme', theme);
    
    // Detect current mode
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const mode = prefersDark ? 'dark' : 'light';
    
    // Apply theme
    applyTheme(theme, mode);
    
    // Show notification
    showNotification(`Theme geändert zu: ${getThemeName(theme)}`);
}

function applyTheme(theme, mode) {
    const html = document.documentElement;
    html.setAttribute('data-theme', theme);
    html.setAttribute('data-mode', mode);
}

function getThemeName(theme) {
    const themeNames = {
        'pride': '🏳️‍🌈 Pride',
        'trans': '🏳️‍⚧️ Trans',
        'lesbian': '🧡 Lesbian',
        'forest': '🌲 Forest',
        'ocean': '🌊 Ocean'
    };
    return themeNames[theme] || theme;
}

// ============================================
// END THEME MANAGEMENT
// ============================================

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
    const statusEl = document.getElementById('backend-status');
    const indicatorEl = document.getElementById('backend-indicator');
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
        
        const response = await fetch(`${API_URL}/health`, { 
            method: 'GET',
            mode: 'cors',
            cache: 'no-cache',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            statusEl.classList.add('online');
            statusEl.classList.remove('offline');
            indicatorEl.textContent = 'Online ✓';
        } else {
            throw new Error(`Backend not healthy: ${response.status}`);
        }
    } catch (error) {
        statusEl.classList.add('offline');
        statusEl.classList.remove('online');
        
        if (error.name === 'AbortError') {
            indicatorEl.textContent = 'Offline ✗ (Timeout)';
            console.error('Backend health check timeout after 15s - retrying in 10s', 'URL:', `${API_URL}/health`);
        } else {
            indicatorEl.textContent = 'Offline ✗';
            console.error('Backend health check error:', error.message, 'URL:', `${API_URL}/health`);
        }
        // Automatic retry after 10 seconds for all errors
        setTimeout(checkBackendStatus, 10000);
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
                output_path: 'Downloads',
                use_timestamped_folder: true  // Web app uses timestamped folders
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
            
            // Update overall progress bar
            updateVideoProgress(status.progress);
            updateVideoStatus(status.message);
            
            // Update current file progress bar
            if (status.current_file_progress !== undefined) {
                updateVideoCurrentProgress(status.current_file_progress);
                updateVideoCurrentStatus(status.current_file_message || '');
            }
            
            // Check if download is complete
            if (status.status === 'complete') {
                // Stop polling
                clearInterval(interval);
                
                const button = document.getElementById('video-download-btn');
                button.disabled = false;
                button.textContent = 'Download starten';
                
                // Reset current file progress
                updateVideoCurrentProgress(0);
                updateVideoCurrentStatus('');
                
                // Update status message
                updateVideoStatus(`Download abgeschlossen! Fehlgeschlagen: ${status.failed_urls.length}`);
                
                // Reset task ID
                currentVideoTaskId = null;
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

function updateVideoCurrentProgress(progress) {
    const fill = document.querySelector('#video-current-progress-bar .progress-fill');
    fill.style.width = `${progress}%`;
    fill.textContent = `${Math.round(progress)}%`;
}

function updateVideoCurrentStatus(message) {
    document.getElementById('video-current-status').textContent = message;
}

// Audio download
async function startAudioDownload() {
    if (audioUrls.length === 0) {
        alert('Bitte fügen Sie mindestens eine URL hinzu.');
        return;
    }
    
    const format = document.querySelector('input[name="audio-format"]:checked').value;
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
                output_path: 'Downloads',
                use_timestamped_folder: true  // Web app uses timestamped folders
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
            
            // Update overall progress bar
            updateAudioProgress(status.progress);
            updateAudioStatus(status.message);
            
            // Update current file progress bar
            if (status.current_file_progress !== undefined) {
                updateAudioCurrentProgress(status.current_file_progress);
                updateAudioCurrentStatus(status.current_file_message || '');
            }
            
            // Check if download is complete
            if (status.status === 'complete') {
                // Stop polling
                clearInterval(interval);
                
                const button = document.getElementById('audio-download-btn');
                button.disabled = false;
                button.textContent = 'Download starten';
                
                // Reset current file progress
                updateAudioCurrentProgress(0);
                updateAudioCurrentStatus('');
                
                // Update status message
                updateAudioStatus(`Download abgeschlossen! Fehlgeschlagen: ${status.failed_urls.length}`);
                
                // Reset task ID
                currentAudioTaskId = null;
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

function updateAudioCurrentProgress(progress) {
    const fill = document.querySelector('#audio-current-progress-bar .progress-fill');
    fill.style.width = `${progress}%`;
    fill.textContent = `${Math.round(progress)}%`;
}

function updateAudioCurrentStatus(message) {
    document.getElementById('audio-current-status').textContent = message;
}

// YouTube Search
let currentSearchController = null;
let currentResultCount = 0;

async function searchYoutube() {
    const input = document.getElementById('search-input');
    const query = input.value.trim();
    
    if (!query) {
        alert('Bitte geben Sie einen Suchbegriff ein.');
        return;
    }
    
    // Cancel previous search if running
    if (currentSearchController) {
        currentSearchController.abort();
        currentSearchController = null;
    }
    
    const statusEl = document.getElementById('search-status');
    const resultsEl = document.getElementById('search-results');
    
    statusEl.innerHTML = '<span class="spinner"></span> Suche läuft...';
    resultsEl.innerHTML = '';
    currentResultCount = 0;
    
    currentSearchController = new AbortController();
    
    // Set 30-second timeout for search
    const searchTimeoutId = setTimeout(() => {
        currentSearchController.abort();
    }, 30000);
    
    try {
        const response = await fetch(`${API_URL}/api/search/youtube`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, max_results: 20 }),
            signal: currentSearchController.signal
        });
        
        if (!response.ok) {
            throw new Error('Suche fehlgeschlagen');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = ''; // Buffer for incomplete lines
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            
            const lines = buffer.split('\n');
            // Keep the last potentially incomplete line in the buffer
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        
                        if (data.error) {
                            statusEl.innerHTML = `Fehler: ${data.error}`;
                            clearTimeout(searchTimeoutId);
                            break;
                        }
                        
                        if (data.done) {
                            statusEl.textContent = `${currentResultCount} Ergebnisse gefunden`;
                            currentSearchController = null;
                            clearTimeout(searchTimeoutId);
                            break;
                        }
                        
                        if (data.title) {
                            appendSearchResult(data);
                            currentResultCount++;
                            statusEl.innerHTML = `<span class="spinner"></span> ${currentResultCount} Ergebnisse gefunden...`;
                        }
                    } catch (parseError) {
                        console.error('Failed to parse SSE data:', line, parseError);
                    }
                }
            }
        }
        
    } catch (error) {
        clearTimeout(searchTimeoutId);
        
        if (error.name === 'AbortError') {
            statusEl.textContent = 'Suche hat zu lange gedauert (Timeout nach 30s)';
        } else {
            statusEl.textContent = `Fehler: ${error.message}`;
            console.error('Search error:', error);
        }
        currentSearchController = null;
    }
}

function appendSearchResult(video) {
    const resultsEl = document.getElementById('search-results');
    
    const resultDiv = document.createElement('div');
    resultDiv.className = 'search-result-item';
    resultDiv.style.opacity = '0';
    resultDiv.style.transform = 'translateY(10px)';
    
    // Escape quotes in title and URL for onclick handlers
    const escapedUrl = video.url.replace(/'/g, "\\'");
    const escapedTitle = video.title.replace(/'/g, "\\'").replace(/"/g, '&quot;');
    
    resultDiv.innerHTML = `
        <img src="${video.thumbnail}" alt="${escapedTitle}" class="result-thumbnail">
        <div class="result-info">
            <h3 class="result-title">${video.title}</h3>
            <p class="result-duration">Dauer: ${video.duration}</p>
            <p class="result-url">${video.url}</p>
        </div>
        <div class="result-actions">
            <button onclick="addToVideoList('${escapedUrl}')" class="btn-add-video" title="Zur Video-Liste hinzufügen">📹 Video</button>
            <button onclick="addToAudioList('${escapedUrl}')" class="btn-add-audio" title="Zur Audio-Liste hinzufügen">🎵 Audio</button>
        </div>
    `;
    
    resultsEl.appendChild(resultDiv);
    
    // Animate in
    setTimeout(() => {
        resultDiv.style.transition = 'all 0.3s ease';
        resultDiv.style.opacity = '1';
        resultDiv.style.transform = 'translateY(0)';
    }, 10);
}

function addToVideoList(url) {
    if (!videoUrls.includes(url)) {
        videoUrls.push(url);
        updateVideoUrlList();
        showNotification('Zur Video-Liste hinzugefügt');
    } else {
        showNotification('Bereits in Video-Liste vorhanden');
    }
}


function addToAudioList(url) {
    if (!audioUrls.includes(url)) {
        audioUrls.push(url);
        updateAudioUrlList();
        showNotification('Zur Audio-Liste hinzugefügt');
    } else {
        showNotification('Bereits in Audio-Liste vorhanden');
    }
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 10);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}
