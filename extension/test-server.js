// Test WebSocket Server for Video Capture Extension
// Now receives TEXT transcripts instead of audio chunks
// Usage: node test-server.js

const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const OUTPUT_DIR = './captured-data';

// Create output directory
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const server = new WebSocket.Server({ port: PORT });

console.log(`\n🚀 WebSocket Server running on ws://localhost:${PORT}\n`);
console.log(`📝 Receiving TEXT transcripts from extension (STT done client-side)`);
console.log('Waiting for connections...\n');

server.on('connection', (ws, req) => {
  console.log('✅ Client connected from:', req.socket.remoteAddress);

  // Session state
  const session = {
    id: Date.now(),
    frameCount: 0,
    transcriptCount: 0,
    transcriptHistory: [],
  };

  // Initialize transcript file for this session
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

      } else if (message.type === 'transcript') {
        // Receive transcript TEXT from extension (already processed by ElevenLabs)
        session.transcriptCount++;
        const startTimeFormatted = formatTime(message.videoTimeStart);
        const endTimeFormatted = formatTime(message.videoTimeEnd);
        const text = message.text || '';

        console.log(`\n💬 Transcript #${session.transcriptCount}`);
        console.log(`   [${startTimeFormatted} - ${endTimeFormatted}]`);
        console.log(`   "${text}"\n`);

        // Save to transcript history
        session.transcriptHistory.push(text);

        // Append to transcript file
        const line = `[${startTimeFormatted} - ${endTimeFormatted}] ${text}\n`;
        fs.appendFileSync(session.transcriptPath, line);

      } else {
        console.log('📨 Unknown message type:', message.type);
      }

    } catch (error) {
      console.error('❌ Failed to parse message:', error.message);
    }
  });

  ws.on('close', () => {
    // Finalize transcript file
    if (session.transcriptHistory.length > 0) {
      fs.appendFileSync(session.transcriptPath, `\n=== End of Session ===\n`);
    }

    console.log(`\n👋 Client disconnected`);
    console.log(`   Session ID: ${session.id}`);
    console.log(`   Total frames received: ${session.frameCount}`);
    console.log(`   Total transcripts received: ${session.transcriptCount}\n`);
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
    const base64Data = message.image.replace(/^data:image\/jpeg;base64,/, '');
    const filename = `frame_${sessionId}_${index.toString().padStart(4, '0')}_${Math.floor(message.videoTime)}s.jpg`;
    const filepath = path.join(OUTPUT_DIR, filename);

    fs.writeFileSync(filepath, base64Data, 'base64');
    console.log(`   💾 Saved: ${filename}`);
  } catch (error) {
    console.error('   ❌ Failed to save frame:', error.message);
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
