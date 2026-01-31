// Offscreen Document - Audio Capture using MediaRecorder + ElevenLabs STT

import { MSG, CONFIG } from './types.js';

class AudioCapturer {
  constructor() {
    this.mediaRecorder = null;
    this.stream = null;
    this.currentVideoTime = 0;
    this.chunkStartTime = 0;
    this.isPaused = false;
    this.isProcessingSTT = false;
    this.sttQueue = []; // 큐로 청크를 순차 처리

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
    const duration = CONFIG.AUDIO_CHUNK_DURATION;
    const videoTimeStart = this.chunkStartTime;
    const videoTimeEnd = videoTimeStart + duration;

    // Update chunk start time for next chunk
    this.chunkStartTime = this.currentVideoTime;

    // WebM 헤더 검증 (손상된 청크 필터링)
    const arrayBuffer = await blob.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);
    const hasWebMHeader = bytes.length >= 4 && 
                          bytes[0] === 0x1a && bytes[1] === 0x45 && 
                          bytes[2] === 0xdf && bytes[3] === 0xa3;

    if (!hasWebMHeader) {
      console.log('[Offscreen] ⏭️  Skipping chunk without WebM header (length:', bytes.length, ')');
      return;
    }

    // 큐에 추가하고 처리 시작
    this.sttQueue.push({ blob, videoTimeStart, videoTimeEnd });
    console.log('[Offscreen] Audio chunk added to queue:', {
      duration,
      videoTimeStart,
      videoTimeEnd,
      queueSize: this.sttQueue.length,
      isProcessing: this.isProcessingSTT,
      blobSize: blob.size,
      hasWebMHeader: true
    });

    this.processQueue();
  }

  async processQueue() {
    // 이미 처리 중이면 리턴 (큐는 유지됨)
    if (this.isProcessingSTT) {
      return;
    }

    // 큐가 비었으면 리턴
    if (this.sttQueue.length === 0) {
      return;
    }

    this.isProcessingSTT = true;

    // 큐에서 하나 꺼내서 처리
    const { blob, videoTimeStart, videoTimeEnd } = this.sttQueue.shift();

    try {
      console.log('[Offscreen] Processing STT for', videoTimeStart, '-', videoTimeEnd, '(remaining:', this.sttQueue.length, ')');
      console.log('[Offscreen] API URL:', CONFIG.ELEVENLABS_API_URL);
      console.log('[Offscreen] API Key:', CONFIG.ELEVENLABS_API_KEY ? '***' : 'NOT SET');
      console.log('[Offscreen] Blob size:', blob.size, 'bytes');

      // Create FormData for ElevenLabs API
      const formData = new FormData();
      formData.append('file', blob, 'audio.webm');
      formData.append('model_id', 'scribe_v1');
      formData.append('language_code', 'ko');

      // Call ElevenLabs STT API
      console.log('[Offscreen] Calling ElevenLabs API...');
      const response = await fetch(CONFIG.ELEVENLABS_API_URL, {
        method: 'POST',
        headers: {
          'xi-api-key': CONFIG.ELEVENLABS_API_KEY,
        },
        body: formData,
      });

      console.log('[Offscreen] API Response Status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[Offscreen] API Error Response:', errorText);
        throw new Error(`ElevenLabs API error: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log('[Offscreen] API Response JSON:', result);
      const text = result.text?.trim() || '';

      if (text) {
        console.log('[Offscreen] STT result:', text);

        // Send transcript result to background
        this.sendMessage({
          source: 'offscreen',
          type: MSG.TRANSCRIPT_RESULT,
          videoTimeStart,
          videoTimeEnd,
          text,
        });
      } else {
        console.log('[Offscreen] STT returned empty text');
      }

    } catch (error) {
      console.error('[Offscreen] STT failed:', error);
      this.sendMessage({
        source: 'offscreen',
        type: MSG.AUDIO_ERROR,
        error: error.message,
      });
    } finally {
      this.isProcessingSTT = false;
      // 다음 항목 처리 - 재귀적으로 큐의 다음 항목 처리
      setTimeout(() => this.processQueue(), 100);
    }
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
    this.sttQueue = []; // 큐 클리어
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
