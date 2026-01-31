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
  TRANSCRIPT_RESULT: 'TRANSCRIPT_RESULT',

  // Background → Content
  REQUEST_STATUS: 'REQUEST_STATUS',

  // WebSocket (Popup → Background)
  SET_WS_URL: 'SET_WS_URL',
  CONNECT_WS: 'CONNECT_WS',
  DISCONNECT_WS: 'DISCONNECT_WS',
};

// WebSocket Data Protocol (Extension ↔ Server)
// =============================================
//
// Extension → Server:
// 1. Frame message (화면 캡처 이미지):
//    {
//      "type": "frame",
//      "timestamp": 1234567890,        // Unix timestamp (ms)
//      "videoTime": 123.45,            // Current video time (seconds)
//      "image": "data:image/jpeg;base64,...",  // Base64 JPEG image
//      "capturedAt": 1234567890        // Capture timestamp (ms)
//    }
//
// 2. Transcript message (ElevenLabs STT 결과 텍스트):
//    {
//      "type": "transcript",
//      "timestamp": 1234567890,        // Unix timestamp (ms)
//      "videoTime": 123.45,            // Current video time (seconds)
//      "videoTimeStart": 120.0,        // Audio chunk start time (seconds)
//      "videoTimeEnd": 125.0,          // Audio chunk end time (seconds)
//      "text": "transcribed text"      // STT result text
//    }
//
// Server → Extension:
// 1. Command message (optional):
//    {
//      "type": "command",
//      "action": "pause" | "resume" | "seek",
//      "value": 123.45                 // For seek: target time
//    }
//

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

  // ElevenLabs STT API
  ELEVENLABS_API_KEY: 'sk_b14cb79ba4fb5cf5fb3ff1c91d424cf4cfb2ed04064a8660',
  ELEVENLABS_API_URL: 'https://api.elevenlabs.io/v1/speech-to-text',
};
