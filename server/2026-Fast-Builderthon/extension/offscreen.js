// Offscreen Document - Audio Capture using MediaRecorder

import { MSG, CONFIG } from './types.js';

class AudioCapturer {
  constructor() {
    this.mediaRecorder = null;
    this.stream = null;
    this.currentVideoTime = 0;
    this.chunkStartTime = 0;
    this.isPaused = false;
    this.chunks = [];

    this.setupMessageListener();
  }

  setupMessageListener() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      // Only handle messages targeted at offscreen
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

      // Get media stream from tab
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          mandatory: {
            chromeMediaSource: 'tab',
            chromeMediaSourceId: streamId,
          },
        },
        video: false,
      });

      // Create MediaRecorder
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      this.chunks = [];

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

      // Start recording with timeslice for chunked data
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
    // Convert blob to base64 for message passing
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1];
      const duration = CONFIG.AUDIO_CHUNK_DURATION;

      this.sendMessage({
        source: 'offscreen',
        type: MSG.AUDIO_CHUNK,
        videoTimeStart: this.chunkStartTime,
        duration: duration,
        data: base64,
        mimeType: 'audio/webm;codecs=opus',
      });

      console.log('[Offscreen] Audio chunk sent, start time:', this.chunkStartTime);

      // Update chunk start time for next chunk
      this.chunkStartTime = this.currentVideoTime;
    };

    reader.readAsDataURL(blob);
  }

  stopCapture() {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }

    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    this.mediaRecorder = null;
    this.chunks = [];
    console.log('[Offscreen] Audio capture stopped');
  }

  syncTime(videoTime, paused, playbackRate) {
    this.currentVideoTime = videoTime;

    // If there's a significant time jump (seek), finish current chunk and start new
    if (Math.abs(videoTime - this.chunkStartTime) > CONFIG.AUDIO_CHUNK_DURATION + 1) {
      console.log('[Offscreen] Time jump detected, restarting chunk');

      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        // Request data and restart
        this.mediaRecorder.requestData();
        this.chunkStartTime = videoTime;
      }
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

// Initialize capturer
const capturer = new AudioCapturer();
console.log('[Offscreen] Audio capturer initialized');
