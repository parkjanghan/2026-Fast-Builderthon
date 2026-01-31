// Offscreen Document - Audio Capture with ElevenLabs STT

import { MSG, CONFIG } from './types.js';

// ElevenLabs STT Configuration
const STT_CONFIG = {
  API_KEY: 'sk_b14cb79ba4fb5cf5fb3ff1c91d424cf4cfb2ed04064a8660',
  API_URL: 'https://api.elevenlabs.io/v1/speech-to-text',
  PROCESS_INTERVAL: 2, // Process STT every N chunks (10 seconds)
  MAX_BUFFER_CHUNKS: 24, // Max 2 minutes buffer
};

class AudioCapturer {
  constructor() {
    this.mediaRecorder = null;
    this.stream = null;
    this.currentVideoTime = 0;
    this.chunkStartTime = 0;
    this.isPaused = false;

    // Audio buffer for STT
    this.audioBuffer = [];
    this.chunkCount = 0;
    this.isProcessingSTT = false;
    this.firstChunkTime = null;

    this.setupMessageListener();
  }

  setupMessageListener() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.target !== 'offscreen') return;

      switch (message.type) {
        case MSG.START_AUDIO:
          this.startCapture(message.streamId, message.videoTime);
          break;
        case MSG.STOP_AUDIO:
          this.stopCapture();
          break;
        case MSG.SYNC_TIME:
          this.syncTime(message.videoTime, message.paused, message.playbackRate);
          break;
        case MSG.PAUSE_AUDIO:
          this.pause();
          break;
        case MSG.RESUME_AUDIO:
          this.resume();
          break;
      }
    });
  }

  async startCapture(streamId, videoTime) {
    try {
      this.currentVideoTime = videoTime || 0;
      this.chunkStartTime = this.currentVideoTime;
      this.audioBuffer = [];
      this.chunkCount = 0;
      this.firstChunkTime = null;

      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          mandatory: {
            chromeMediaSource: 'tab',
            chromeMediaSourceId: streamId,
          },
        },
        video: false,
      });

      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.handleAudioData(event.data);
        }
      };

      this.mediaRecorder.onerror = (event) => {
        console.error('[Offscreen] MediaRecorder error:', event.error);
        this.sendMessage({
          source: 'offscreen',
          type: MSG.AUDIO_ERROR,
          error: event.error.message,
        });
      };

      this.mediaRecorder.start(CONFIG.AUDIO_CHUNK_DURATION * 1000);
      console.log('[Offscreen] Audio capture started');
    } catch (error) {
      console.error('[Offscreen] Failed to start capture:', error);
      this.sendMessage({
        source: 'offscreen',
        type: MSG.AUDIO_ERROR,
        error: error.message,
      });
    }
  }

  async handleAudioData(blob) {
    this.chunkCount++;

    // Convert blob to ArrayBuffer
    const arrayBuffer = await blob.arrayBuffer();
    const buffer = new Uint8Array(arrayBuffer);

    // Check for valid WebM header on first chunk or after reset
    if (this.audioBuffer.length === 0) {
      if (!this.isValidWebMHeader(buffer)) {
        console.log('[Offscreen] Skipping chunk (no WebM header)');
        return;
      }
      this.firstChunkTime = this.chunkStartTime;
      console.log('[Offscreen] Valid WebM header detected');
    }

    // Add to buffer
    this.audioBuffer.push({
      buffer,
      videoTime: this.chunkStartTime,
      duration: CONFIG.AUDIO_CHUNK_DURATION,
    });

    console.log(`[Offscreen] Audio chunk #${this.chunkCount} | Buffer: ${this.audioBuffer.length}/${STT_CONFIG.MAX_BUFFER_CHUNKS}`);

    // Update chunk start time
    this.chunkStartTime = this.currentVideoTime;

    // Process STT periodically
    if (this.chunkCount % STT_CONFIG.PROCESS_INTERVAL === 0) {
      this.processSTT();
    }

    // Reset buffer if full
    if (this.audioBuffer.length >= STT_CONFIG.MAX_BUFFER_CHUNKS) {
      console.log('[Offscreen] Buffer full, resetting...');
      this.audioBuffer = [];
      this.firstChunkTime = null;
    }
  }

  isValidWebMHeader(buffer) {
    if (buffer.length < 4) return false;
    return buffer[0] === 0x1a && buffer[1] === 0x45 && buffer[2] === 0xdf && buffer[3] === 0xa3;
  }

  combineAudioChunks() {
    const totalLength = this.audioBuffer.reduce((sum, chunk) => sum + chunk.buffer.length, 0);
    const combined = new Uint8Array(totalLength);

    let offset = 0;
    for (const chunk of this.audioBuffer) {
      combined.set(chunk.buffer, offset);
      offset += chunk.buffer.length;
    }

    return combined;
  }

  async processSTT() {
    if (this.isProcessingSTT || this.audioBuffer.length === 0) {
      return;
    }

    this.isProcessingSTT = true;

    try {
      const combinedBuffer = this.combineAudioChunks();
      const startTime = this.firstChunkTime || 0;
      const lastChunk = this.audioBuffer[this.audioBuffer.length - 1];
      const endTime = lastChunk.videoTime + lastChunk.duration;

      console.log(`[Offscreen] Processing STT (${this.audioBuffer.length} chunks, ${combinedBuffer.length} bytes)...`);

      // Create form data for ElevenLabs API
      const blob = new Blob([combinedBuffer], { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('file', blob, 'audio.webm');
      formData.append('model_id', 'scribe_v1');
      formData.append('language_code', 'ko');

      // Call ElevenLabs STT API
      const response = await fetch(STT_CONFIG.API_URL, {
        method: 'POST',
        headers: {
          'xi-api-key': STT_CONFIG.API_KEY,
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
        console.log(`[Offscreen] STT Result: "${text}"`);

        // Send transcript to background
        this.sendMessage({
          source: 'offscreen',
          type: MSG.TRANSCRIPT,
          text: text,
          videoTimeStart: startTime,
          videoTimeEnd: endTime,
        });
      }
    } catch (error) {
      console.error('[Offscreen] STT failed:', error.message);
      this.sendMessage({
        source: 'offscreen',
        type: MSG.TRANSCRIPT_ERROR,
        error: error.message,
      });
    } finally {
      this.isProcessingSTT = false;
    }
  }

  stopCapture() {
    // Process remaining audio before stopping
    if (this.audioBuffer.length > 0 && !this.isProcessingSTT) {
      this.processSTT();
    }

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }

    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    this.mediaRecorder = null;
    this.audioBuffer = [];
    console.log('[Offscreen] Audio capture stopped');
  }

  syncTime(videoTime, paused, playbackRate) {
    this.currentVideoTime = videoTime;

    if (Math.abs(videoTime - this.chunkStartTime) > CONFIG.AUDIO_CHUNK_DURATION + 1) {
      console.log('[Offscreen] Time jump detected, resetting buffer');
      // Process current buffer before reset
      if (this.audioBuffer.length > 0) {
        this.processSTT();
      }
      this.audioBuffer = [];
      this.firstChunkTime = null;
      this.chunkStartTime = videoTime;
    }
  }

  pause() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.pause();
      this.isPaused = true;
      console.log('[Offscreen] Audio capture paused');
    }
  }

  resume() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
      this.mediaRecorder.resume();
      this.isPaused = false;
      this.chunkStartTime = this.currentVideoTime;
      console.log('[Offscreen] Audio capture resumed');
    }
  }

  sendMessage(message) {
    try {
      chrome.runtime.sendMessage(message);
    } catch (error) {
      console.error('[Offscreen] Failed to send message:', error);
    }
  }
}

const capturer = new AudioCapturer();
console.log('[Offscreen] Audio capturer initialized with ElevenLabs STT');
