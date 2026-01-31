// Message Types
export const MSG = {
  // Content → Background
  VIDEO_FOUND: 'VIDEO_FOUND',
  VIDEO_LOST: 'VIDEO_LOST',
  VIDEO_STATUS: 'VIDEO_STATUS',

  // Popup → Background
  START_CAPTURE: 'START_CAPTURE',
  STOP_CAPTURE: 'STOP_CAPTURE',
  GET_STATE: 'GET_STATE',

  // Background → Offscreen
  START_AUDIO: 'START_AUDIO',
  STOP_AUDIO: 'STOP_AUDIO',
  SYNC_TIME: 'SYNC_TIME',
  PAUSE_AUDIO: 'PAUSE_AUDIO',
  RESUME_AUDIO: 'RESUME_AUDIO',

  // Offscreen → Background
  AUDIO_CHUNK: 'AUDIO_CHUNK',
  AUDIO_ERROR: 'AUDIO_ERROR',

  // Background → Content
  REQUEST_STATUS: 'REQUEST_STATUS',

  // WebSocket (Popup → Background)
  SET_WS_URL: 'SET_WS_URL',
  CONNECT_WS: 'CONNECT_WS',
  DISCONNECT_WS: 'DISCONNECT_WS',
};

// Configuration
export const CONFIG = {
  // Polling interval for video status (ms)
  STATUS_POLL_INTERVAL: 300,

  // Audio chunk duration (seconds)
  AUDIO_CHUNK_DURATION: 5,

  // Frame capture interval (seconds)
  FRAME_CAPTURE_INTERVAL: 5,

  // Offscreen document reasons
  OFFSCREEN_REASON: 'USER_MEDIA',
};
