// Background Service Worker - Central State Management and Message Broker

import { MSG, CONFIG } from './types.js';

// Global state (exposed to console via self.state)
const state = {
  isCapturing: false,
  hasVideo: false,
  currentVideoTime: 0,
  paused: true,
  playbackRate: 1,
  duration: 0,
  tabId: null,
  transcripts: [],
  frames: [],
  frameIntervalId: null,
  // WebSocket
  wsConnected: false,
  // wsUrl: 'wss://5920da4b-c27b-4df6-9297-f7d4ec4f329f-00-st4gdos7kox3.riker.replit.dev/ws',
  wsUrl: 'ws://localhost:8080',
};

// Expose state to console for debugging
self.state = state;

// ============ WebSocket Management ============
let ws = null;
let wsReconnectTimeout = null;

function connectWebSocket() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    return;
  }

  try {
    ws = new WebSocket(state.wsUrl);

    ws.onopen = () => {
      state.wsConnected = true;
      console.log('[WebSocket] Connected to', state.wsUrl);
    };

    ws.onclose = () => {
      state.wsConnected = false;
      console.log('[WebSocket] Disconnected');
      // Auto reconnect after 3 seconds if capturing
      if (state.isCapturing) {
        wsReconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
    };

    ws.onmessage = (event) => {
      console.log('[WebSocket] Received:', event.data);
    };
  } catch (error) {
    console.error('[WebSocket] Failed to connect:', error);
  }
}

function disconnectWebSocket() {
  if (wsReconnectTimeout) {
    clearTimeout(wsReconnectTimeout);
    wsReconnectTimeout = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
  state.wsConnected = false;
}

function sendToWebSocket(type, data) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.log('[WebSocket] Not connected, skipping send');
    return false;
  }

  try {
    const message = JSON.stringify({
      source: 'chrome',
      data: {
        type,
        timestamp: Date.now(),
        videoTime: state.currentVideoTime,
        ...data,
      },
    });
    ws.send(message);
    console.log('[WebSocket] Sent:', type);
    return true;
  } catch (error) {
    console.error('[WebSocket] Send failed:', error);
    return false;
  }
}

function sendFrame(frame) {
  sendToWebSocket('frame', {
    videoTime: frame.videoTime,
    image: frame.image,
    capturedAt: frame.capturedAt,
  });
}

function sendTranscript(transcript) {
  sendToWebSocket('transcript', {
    text: transcript.text,
    videoTimeStart: transcript.videoTimeStart,
    videoTimeEnd: transcript.videoTimeEnd,
  });
}

// Offscreen document management
let creatingOffscreen = null;

async function ensureOffscreenDocument() {
  const offscreenUrl = chrome.runtime.getURL('offscreen.html');

  // Check if offscreen document already exists
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [offscreenUrl],
  });

  if (existingContexts.length > 0) {
    return;
  }

  // Create offscreen document
  if (creatingOffscreen) {
    await creatingOffscreen;
  } else {
    creatingOffscreen = chrome.offscreen.createDocument({
      url: offscreenUrl,
      reasons: [chrome.offscreen.Reason.USER_MEDIA],
      justification: 'Capturing tab audio for video analysis',
    });

    await creatingOffscreen;
    creatingOffscreen = null;
  }
}

async function closeOffscreenDocument() {
  const offscreenUrl = chrome.runtime.getURL('offscreen.html');

  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [offscreenUrl],
  });

  if (existingContexts.length > 0) {
    await chrome.offscreen.closeDocument();
  }
}

// Frame capture using captureVisibleTab
async function captureFrame() {
  if (!state.isCapturing || state.paused || !state.tabId) {
    return;
  }

  try {
    const dataUrl = await chrome.tabs.captureVisibleTab(null, {
      format: 'jpeg',
      quality: 80,
    });

    const frame = {
      videoTime: state.currentVideoTime,
      image: dataUrl,
      capturedAt: Date.now(),
    };

    state.frames.push(frame);
    console.log('[Background] Frame captured at video time:', state.currentVideoTime);

    // Send frame via WebSocket
    sendFrame(frame);
  } catch (error) {
    console.error('[Background] Frame capture failed:', error);
  }
}

function startFrameCapture() {
  stopFrameCapture();

  // Capture immediately
  captureFrame();

  // Then capture at interval
  state.frameIntervalId = setInterval(captureFrame, CONFIG.FRAME_CAPTURE_INTERVAL * 1000);
}

function stopFrameCapture() {
  if (state.frameIntervalId) {
    clearInterval(state.frameIntervalId);
    state.frameIntervalId = null;
  }
}

// Start capture process
async function startCapture(tabId) {
  if (state.isCapturing) {
    console.log('[Background] Already capturing');
    return { success: false, error: 'Already capturing' };
  }

  state.tabId = tabId;

  try {
    // Create offscreen document for audio capture
    await ensureOffscreenDocument();

    // Get stream ID for tab capture
    const streamId = await chrome.tabCapture.getMediaStreamId({
      targetTabId: tabId,
    });

    // Start audio capture in offscreen document
    await chrome.runtime.sendMessage({
      target: 'offscreen',
      type: MSG.START_AUDIO,
      streamId,
      videoTime: state.currentVideoTime,
    });

    state.isCapturing = true;

    // Connect WebSocket
    connectWebSocket();

    // Start frame capture if video is playing
    if (!state.paused) {
      startFrameCapture();
    }

    console.log('[Background] Capture started');
    return { success: true };
  } catch (error) {
    console.error('[Background] Failed to start capture:', error);
    return { success: false, error: error.message };
  }
}

// Stop capture process
async function stopCapture() {
  if (!state.isCapturing) {
    return { success: true };
  }

  try {
    // Stop frame capture
    stopFrameCapture();

    // Stop audio capture
    await chrome.runtime.sendMessage({
      target: 'offscreen',
      type: MSG.STOP_AUDIO,
    });

    // Close offscreen document
    await closeOffscreenDocument();

    // Disconnect WebSocket
    disconnectWebSocket();

    const result = {
      success: true,
      transcripts: state.transcripts.length,
      frames: state.frames.length,
    };

    // Clear collected data to free memory
    state.transcripts = [];
    state.frames = [];

    state.isCapturing = false;
    console.log('[Background] Capture stopped');

    return result;
  } catch (error) {
    console.error('[Background] Failed to stop capture:', error);
    state.isCapturing = false;
    return { success: false, error: error.message };
  }
}

// Handle video status updates from content script
function handleVideoStatus(message, sender) {
  const previousPaused = state.paused;

  state.currentVideoTime = message.currentTime;
  state.paused = message.paused;
  state.playbackRate = message.playbackRate;
  state.duration = message.duration;

  if (sender.tab) {
    state.tabId = sender.tab.id;
  }

  // Sync time with offscreen document
  if (state.isCapturing) {
    chrome.runtime.sendMessage({
      target: 'offscreen',
      type: MSG.SYNC_TIME,
      videoTime: state.currentVideoTime,
      paused: state.paused,
      playbackRate: state.playbackRate,
    });

    // Handle pause/play state changes
    if (message.event === 'pause' || (state.paused && !previousPaused)) {
      stopFrameCapture();
      chrome.runtime.sendMessage({
        target: 'offscreen',
        type: MSG.PAUSE_AUDIO,
      });
    } else if (message.event === 'play' || (!state.paused && previousPaused)) {
      startFrameCapture();
      chrome.runtime.sendMessage({
        target: 'offscreen',
        type: MSG.RESUME_AUDIO,
      });
    }

    // Handle seek
    if (message.event === 'seeked') {
      console.log('[Background] Seek detected, resync at:', state.currentVideoTime);
    }
  }
}

// Message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Messages from offscreen document
  if (message.source === 'offscreen') {
    if (message.type === MSG.TRANSCRIPT) {
      const transcript = {
        text: message.text,
        videoTimeStart: message.videoTimeStart,
        videoTimeEnd: message.videoTimeEnd,
      };
      state.transcripts.push(transcript);
      console.log('[Background] Transcript received:', message.text);

      // Send transcript via WebSocket (text only, not audio)
      sendTranscript(transcript);
    } else if (message.type === MSG.AUDIO_ERROR || message.type === MSG.TRANSCRIPT_ERROR) {
      console.error('[Background] Error:', message.error);
    }
    return;
  }

  // Messages from content script
  if (message.type === MSG.VIDEO_FOUND) {
    state.hasVideo = true;
    console.log('[Background] Video found in tab:', sender.tab?.id);
    sendResponse({ success: true });
    return;
  }

  if (message.type === MSG.VIDEO_LOST) {
    state.hasVideo = false;
    if (state.isCapturing) {
      stopCapture();
    }
    console.log('[Background] Video lost');
    sendResponse({ success: true });
    return;
  }

  if (message.type === MSG.VIDEO_STATUS) {
    handleVideoStatus(message, sender);
    return;
  }

  // Messages from popup
  if (message.type === MSG.START_CAPTURE) {
    startCapture(message.tabId).then(sendResponse);
    return true; // Will respond asynchronously
  }

  if (message.type === MSG.STOP_CAPTURE) {
    stopCapture().then(sendResponse);
    return true;
  }

  if (message.type === MSG.GET_STATE) {
    sendResponse({
      isCapturing: state.isCapturing,
      hasVideo: state.hasVideo,
      currentVideoTime: state.currentVideoTime,
      paused: state.paused,
      duration: state.duration,
      transcripts: state.transcripts.length,
      frames: state.frames.length,
      wsConnected: state.wsConnected,
      wsUrl: state.wsUrl,
    });
    return;
  }

  // WebSocket configuration
  if (message.type === MSG.SET_WS_URL) {
    state.wsUrl = message.url;
    console.log('[Background] WebSocket URL set to:', message.url);
    // Reconnect if already connected
    if (state.wsConnected) {
      disconnectWebSocket();
      connectWebSocket();
    }
    sendResponse({ success: true });
    return;
  }

  if (message.type === MSG.CONNECT_WS) {
    connectWebSocket();
    sendResponse({ success: true });
    return;
  }

  if (message.type === MSG.DISCONNECT_WS) {
    disconnectWebSocket();
    sendResponse({ success: true });
    return;
  }
});

console.log('[Background] Service Worker initialized');
