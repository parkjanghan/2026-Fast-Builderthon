// Test WebSocket Server for Video Capture Extension
// Usage: node test-server.js

const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
const fetch = require('node-fetch');

const PORT = 8080;
const OUTPUT_DIR = './captured-data';

// Configuration
const CONFIG = {
  // Max audio buffer: keep last N chunks (each chunk = 5 seconds)
  MAX_BUFFER_CHUNKS: 24, // 2 minutes max (24 * 5s = 120s)
  // ElevenLabs STT settings
  ELEVENLABS_API_KEY: process.env.ELEVENLABS_API_KEY || 'sk_b14cb79ba4fb5cf5fb3ff1c91d424cf4cfb2ed04064a8660',
  ELEVENLABS_API_URL: 'https://api.elevenlabs.io/v1/speech-to-text',
  // Process STT every N chunks (to avoid too frequent API calls)
  STT_PROCESS_INTERVAL: 2, // Process every 2 chunks (10 seconds)
};

// Create output directory
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const server = new WebSocket.Server({ port: PORT });

console.log(`\n🚀 WebSocket Server running on ws://localhost:${PORT}\n`);
console.log(`📋 Config: Window=${CONFIG.WINDOW_SIZE * 5}s, STT every ${CONFIG.STT_PROCESS_INTERVAL * 5}s`);
console.log(`🎤 Using ElevenLabs Scribe for STT`);
console.log('Waiting for connections...\n');

server.on('connection', (ws, req) => {
  console.log('✅ Client connected from:', req.socket.remoteAddress);

  // Session state
  const session = {
    id: Date.now(),
    frameCount: 0,
    audioCount: 0,
    audioStream: null,
    audioFilePath: null,
    firstAudioTime: null,
    // Audio buffer for STT (accumulate all chunks)
    audioBuffer: [], // All audio chunks in order
    lastProcessedIndex: 0, // Track which chunks have been processed
    transcriptHistory: [], // Accumulated transcripts
    isProcessingSTT: false,
  };

  // Initialize audio file stream for this session
  session.audioFilePath = path.join(OUTPUT_DIR, `audio_session_${session.id}.webm`);
  session.audioStream = fs.createWriteStream(session.audioFilePath);
  console.log(`🎙️  Audio stream: ${session.audioFilePath}`);

  // Initialize transcript file for real-time updates
  session.transcriptPath = path.join(OUTPUT_DIR, `transcript_${session.id}.txt`);
  fs.writeFileSync(session.transcriptPath, `=== Transcript Session ${session.id} ===\n\n`);
  console.log(`📝 Transcript file: ${session.transcriptPath}`);

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);

      if (message.type === 'frame') {
        session.frameCount++;
        const videoTimeFormatted = formatTime(message.videoTime);
        console.log(`📷 Frame #${session.frameCount} | Video Time: ${videoTimeFormatted}`);

        // Save frame image
        saveFrame(message, session.frameCount, session.id);

      } else if (message.type === 'audio') {
        session.audioCount++;
        const startTimeFormatted = formatTime(message.videoTimeStart);

        // Track first audio time
        if (session.firstAudioTime === null) {
          session.firstAudioTime = message.videoTimeStart;
        }

        console.log(`🔊 Audio #${session.audioCount} | Start: ${startTimeFormatted} | Duration: ${message.duration}s`);

        // Append audio chunk to stream (for full recording)
        appendAudioChunk(session, message);

        // Add to audio buffer for STT
        addToAudioBuffer(session, message);

        // Process STT periodically
        if (session.audioCount % CONFIG.STT_PROCESS_INTERVAL === 0) {
          processSTT(session, ws);
        }

      } else {
        console.log('📨 Unknown message type:', message.type);
      }

    } catch (error) {
      console.error('❌ Failed to parse message:', error.message);
    }
  });

  ws.on('close', () => {
    // Close audio stream
    if (session.audioStream) {
      session.audioStream.end();
      console.log(`\n💾 Audio saved: ${session.audioFilePath}`);
    }

    // Finalize transcript file
    if (session.transcriptHistory.length > 0) {
      fs.appendFileSync(session.transcriptPath, `\n=== End of Session ===\n`);
    }

    console.log(`\n👋 Client disconnected`);
    console.log(`   Session ID: ${session.id}`);
    console.log(`   Total frames received: ${session.frameCount}`);
    console.log(`   Total audio chunks received: ${session.audioCount}\n`);
  });

  ws.on('error', (error) => {
    console.error('❌ WebSocket error:', error.message);
  });
});

// Format seconds to MM:SS
function formatTime(seconds) {
  if (!seconds || !isFinite(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Save frame image to file
function saveFrame(message, index, sessionId) {
  try {
    // Extract base64 data from data URL
    const base64Data = message.image.replace(/^data:image\/jpeg;base64,/, '');
    const filename = `frame_${sessionId}_${index.toString().padStart(4, '0')}_${Math.floor(message.videoTime)}s.jpg`;
    const filepath = path.join(OUTPUT_DIR, filename);

    fs.writeFileSync(filepath, base64Data, 'base64');
    console.log(`   💾 Saved: ${filename}`);
  } catch (error) {
    console.error('   ❌ Failed to save frame:', error.message);
  }
}

// Append audio chunk to session stream
function appendAudioChunk(session, message) {
  try {
    const buffer = Buffer.from(message.data, 'base64');
    session.audioStream.write(buffer);
  } catch (error) {
    console.error('   ❌ Failed to append audio:', error.message);
  }
}

// Check if buffer starts with WebM header
function isValidWebMHeader(buffer) {
  if (buffer.length < 4) return false;
  return buffer[0] === 0x1a && buffer[1] === 0x45 && buffer[2] === 0xdf && buffer[3] === 0xa3;
}

// Add chunk to audio buffer (with max limit)
function addToAudioBuffer(session, message) {
  const buffer = Buffer.from(message.data, 'base64');

  // If buffer is empty, first chunk must have valid WebM header
  if (session.audioBuffer.length === 0) {
    if (!isValidWebMHeader(buffer)) {
      console.log(`   ⏭️  Skipping chunk (no WebM header, waiting for valid start)`);
      return;
    }
    console.log(`   ✅ Valid WebM header detected`);
  }

  // If buffer is full, clear and start fresh (to maintain valid WebM structure)
  if (session.audioBuffer.length >= CONFIG.MAX_BUFFER_CHUNKS) {
    console.log(`   🔄 Buffer full (${CONFIG.MAX_BUFFER_CHUNKS} chunks), resetting...`);
    session.audioBuffer = [];
    // Wait for next valid header
    if (!isValidWebMHeader(buffer)) {
      console.log(`   ⏭️  Waiting for valid WebM header after reset`);
      return;
    }
  }

  session.audioBuffer.push({
    buffer,
    videoTime: message.videoTimeStart,
    duration: message.duration,
  });

  console.log(`   📊 Buffer: ${session.audioBuffer.length}/${CONFIG.MAX_BUFFER_CHUNKS} chunks`);
}

// Combine all audio chunks into single buffer
function combineAudioChunks(chunks) {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.buffer.length, 0);
  const combined = Buffer.alloc(totalLength);

  let offset = 0;
  for (const chunk of chunks) {
    chunk.buffer.copy(combined, offset);
    offset += chunk.buffer.length;
  }

  return combined;
}

// Process STT using ElevenLabs Scribe API
async function processSTT(session, ws) {
  if (session.isProcessingSTT || session.audioBuffer.length === 0) {
    return;
  }

  const apiKey = CONFIG.ELEVENLABS_API_KEY;

  session.isProcessingSTT = true;

  try {
    // Combine all audio chunks (full recording)
    const combinedBuffer = combineAudioChunks(session.audioBuffer);

    // Save to temp file
    const tempFile = path.join(OUTPUT_DIR, `temp_stt_${session.id}.webm`);
    fs.writeFileSync(tempFile, combinedBuffer);

    console.log(`\n🎯 Processing STT (${session.audioBuffer.length} chunks, ${combinedBuffer.length} bytes)...`);

    // Get time range
    const startTime = session.audioBuffer[0].videoTime;
    const lastChunk = session.audioBuffer[session.audioBuffer.length - 1];
    const endTime = lastChunk.videoTime + lastChunk.duration;

    // Create form data for ElevenLabs API
    const formData = new FormData();
    formData.append('file', fs.createReadStream(tempFile), {
      filename: 'audio.webm',
      contentType: 'audio/webm',
    });
    formData.append('model_id', 'scribe_v1');
    formData.append('language_code', 'ko'); // Korean

    // Call ElevenLabs STT API
    const response = await fetch(CONFIG.ELEVENLABS_API_URL, {
      method: 'POST',
      headers: {
        'xi-api-key': apiKey,
        ...formData.getHeaders(),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`ElevenLabs API error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    const text = result.text?.trim() || '';

    if (text) {
      console.log(`\n💬 [${formatTime(startTime)} - ${formatTime(endTime)}]`);
      console.log(`   "${text}"\n`);

      // Add to history (avoid duplicates by checking last entry)
      const lastTranscript = session.transcriptHistory[session.transcriptHistory.length - 1];
      if (text !== lastTranscript) {
        session.transcriptHistory.push(text);

        // Append to transcript file in real-time
        const line = `[${formatTime(startTime)} - ${formatTime(endTime)}] ${text}\n`;
        fs.appendFileSync(session.transcriptPath, line);
        console.log(`   📝 Transcript updated`);

        // Send transcript to client
        ws.send(JSON.stringify({
          type: 'transcript',
          startTime,
          endTime,
          text,
          fullContext: session.transcriptHistory.slice(-5).join(' '), // Last 5 transcripts
        }));
      }
    }

    // Clean up temp file
    try {
      fs.unlinkSync(tempFile);
    } catch (e) {
      // Ignore cleanup errors
    }

  } catch (error) {
    console.error('❌ STT failed:', error.message);
  } finally {
    session.isProcessingSTT = false;
  }
}

// Handle server errors
server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use. Try a different port.`);
  } else {
    console.error('❌ Server error:', error.message);
  }
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n🛑 Shutting down server...');
  server.close(() => {
    console.log('Server closed.');
    process.exit(0);
  });
});
