// Popup UI Logic

const MSG = {
  START_CAPTURE: 'START_CAPTURE',
  STOP_CAPTURE: 'STOP_CAPTURE',
  GET_STATE: 'GET_STATE',
  SET_WS_URL: 'SET_WS_URL',
};

// DOM Elements
const videoStatus = document.getElementById('videoStatus');
const captureStatus = document.getElementById('captureStatus');
const currentTime = document.getElementById('currentTime');
const progressFill = document.getElementById('progressFill');
const audioCount = document.getElementById('audioCount');
const frameCount = document.getElementById('frameCount');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const wsUrlInput = document.getElementById('wsUrl');
const wsDot = document.getElementById('wsDot');
const wsStatusText = document.getElementById('wsStatus');

// State
let updateInterval = null;

// Format time as MM:SS
function formatTime(seconds) {
  if (!seconds || !isFinite(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Update UI with current state
function updateUI(state) {
  // Video status
  if (state.hasVideo) {
    videoStatus.textContent = state.paused ? 'Paused' : 'Playing';
    videoStatus.className = 'status-value ' + (state.paused ? 'inactive' : 'active');
  } else {
    videoStatus.textContent = 'Not found';
    videoStatus.className = 'status-value inactive';
  }

  // Capture status
  if (state.isCapturing) {
    captureStatus.textContent = 'Recording';
    captureStatus.className = 'status-value active';
  } else {
    captureStatus.textContent = 'Stopped';
    captureStatus.className = 'status-value inactive';
  }

  // Time
  currentTime.textContent = `${formatTime(state.currentVideoTime)} / ${formatTime(state.duration)}`;

  // Progress bar
  if (state.duration > 0) {
    const progress = (state.currentVideoTime / state.duration) * 100;
    progressFill.style.width = `${progress}%`;
  } else {
    progressFill.style.width = '0%';
  }

  // Data counts
  audioCount.textContent = state.audioChunks || 0;
  frameCount.textContent = state.frames || 0;

  // Button states
  startBtn.disabled = !state.hasVideo || state.isCapturing;
  stopBtn.disabled = !state.isCapturing;

  // WebSocket status
  if (state.wsConnected) {
    wsDot.classList.add('connected');
    wsStatusText.textContent = 'Connected';
  } else {
    wsDot.classList.remove('connected');
    wsStatusText.textContent = 'Disconnected';
  }

  // Update URL input if not focused
  if (state.wsUrl && document.activeElement !== wsUrlInput) {
    wsUrlInput.value = state.wsUrl;
  }
}

// Get current state from background
async function getState() {
  try {
    const state = await chrome.runtime.sendMessage({ type: MSG.GET_STATE });
    updateUI(state);
  } catch (error) {
    console.error('Failed to get state:', error);
  }
}

// Start capture
async function startCapture() {
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    startBtn.disabled = true;
    startBtn.textContent = 'Starting...';

    const response = await chrome.runtime.sendMessage({
      type: MSG.START_CAPTURE,
      tabId: tab.id,
    });

    if (response.success) {
      getState();
    } else {
      alert('Failed to start capture: ' + response.error);
      getState();
    }

    startBtn.textContent = 'Start Capture';
  } catch (error) {
    console.error('Failed to start capture:', error);
    alert('Failed to start capture: ' + error.message);
    startBtn.textContent = 'Start Capture';
    getState();
  }
}

// Stop capture
async function stopCapture() {
  try {
    stopBtn.disabled = true;
    stopBtn.textContent = 'Stopping...';

    const response = await chrome.runtime.sendMessage({ type: MSG.STOP_CAPTURE });

    if (response.success) {
      console.log(`Capture stopped. Collected ${response.audioChunks} audio chunks and ${response.frames} frames.`);
    }

    stopBtn.textContent = 'Stop';
    getState();
  } catch (error) {
    console.error('Failed to stop capture:', error);
    stopBtn.textContent = 'Stop';
    getState();
  }
}

// Set WebSocket URL
async function setWsUrl() {
  const url = wsUrlInput.value.trim();
  if (!url) return;

  try {
    await chrome.runtime.sendMessage({
      type: MSG.SET_WS_URL,
      url,
    });
    console.log('WebSocket URL set to:', url);
  } catch (error) {
    console.error('Failed to set WebSocket URL:', error);
  }
}

// Event listeners
startBtn.addEventListener('click', startCapture);
stopBtn.addEventListener('click', stopCapture);

// Update WebSocket URL on blur or Enter
wsUrlInput.addEventListener('blur', setWsUrl);
wsUrlInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    setWsUrl();
    wsUrlInput.blur();
  }
});

// Initial state and periodic updates
getState();
updateInterval = setInterval(getState, 500);

// Cleanup on popup close
window.addEventListener('unload', () => {
  if (updateInterval) {
    clearInterval(updateInterval);
  }
});
