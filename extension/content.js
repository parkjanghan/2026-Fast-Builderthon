// Content Script - Video Detection and Status Tracking
// Note: Cannot use ES modules in content scripts

const MSG = {
  VIDEO_FOUND: 'VIDEO_FOUND',
  VIDEO_LOST: 'VIDEO_LOST',
  VIDEO_STATUS: 'VIDEO_STATUS',
  REQUEST_STATUS: 'REQUEST_STATUS',
};

const CONFIG = {
  STATUS_POLL_INTERVAL: 300,
  VIDEO_SEARCH_INTERVAL: 1000, // Retry finding video every 1 second
  VIDEO_SEARCH_MAX_RETRIES: 30, // Stop after 30 seconds
};

class VideoTracker {
  constructor() {
    this.video = null;
    this.pollInterval = null;
    this.observer = null;
    this.lastStatus = null;
    this.searchInterval = null;
    this.searchRetries = 0;

    this.init();
  }

  init() {
    console.log('[VideoCapture] Content script initialized on:', window.location.href);

    // Try to find existing video
    this.findVideo();

    // If no video found, start periodic search
    if (!this.video) {
      this.startVideoSearch();
    }

    // Set up MutationObserver for SPA support
    this.setupObserver();

    // Listen for messages from background
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.type === MSG.REQUEST_STATUS) {
        sendResponse(this.getStatus());
      }
      return true;
    });
  }

  startVideoSearch() {
    console.log('[VideoCapture] Starting periodic video search...');
    this.searchRetries = 0;

    this.searchInterval = setInterval(() => {
      this.searchRetries++;
      console.log('[VideoCapture] Searching for video... attempt', this.searchRetries);

      this.findVideo();

      if (this.video || this.searchRetries >= CONFIG.VIDEO_SEARCH_MAX_RETRIES) {
        this.stopVideoSearch();
      }
    }, CONFIG.VIDEO_SEARCH_INTERVAL);
  }

  stopVideoSearch() {
    if (this.searchInterval) {
      clearInterval(this.searchInterval);
      this.searchInterval = null;
      console.log('[VideoCapture] Stopped video search. Found:', !!this.video);
    }
  }

  findVideo() {
    // Find the largest video element (usually the main player)
    const videos = document.querySelectorAll('video');
    console.log('[VideoCapture] Found', videos.length, 'video element(s)');

    let largestVideo = null;
    let largestArea = 0;

    videos.forEach((video, index) => {
      const rect = video.getBoundingClientRect();
      const area = rect.width * rect.height;
      console.log(`[VideoCapture] Video ${index}: ${rect.width}x${rect.height} = ${area}px²`);

      if (area > largestArea) {
        largestArea = area;
        largestVideo = video;
      }
    });

    if (largestVideo && largestVideo !== this.video) {
      this.stopVideoSearch();
      this.attachToVideo(largestVideo);
    } else if (!largestVideo && this.video) {
      this.detachFromVideo();
    }
  }

  attachToVideo(video) {
    // Detach from previous video if any
    if (this.video) {
      this.detachFromVideo();
    }

    this.video = video;
    console.log('[VideoCapture] Video attached!');
    console.log('[VideoCapture] - src:', video.src || video.currentSrc || '(blob/stream)');
    console.log('[VideoCapture] - duration:', video.duration);
    console.log('[VideoCapture] - paused:', video.paused);

    // Notify background
    this.sendMessage({ type: MSG.VIDEO_FOUND });
    console.log('[VideoCapture] Sent VIDEO_FOUND message to background');

    // Add event listeners
    this.addVideoListeners();

    // Start polling
    this.startPolling();

    // Send initial status
    this.sendStatus();
  }

  detachFromVideo() {
    if (!this.video) return;

    console.log('[VideoCapture] Video lost');

    // Remove event listeners
    this.removeVideoListeners();

    // Stop polling
    this.stopPolling();

    // Notify background
    this.sendMessage({ type: MSG.VIDEO_LOST });

    this.video = null;
    this.lastStatus = null;
  }

  addVideoListeners() {
    if (!this.video) return;

    this.video.addEventListener('play', this.handlePlay);
    this.video.addEventListener('pause', this.handlePause);
    this.video.addEventListener('seeking', this.handleSeeking);
    this.video.addEventListener('seeked', this.handleSeeked);
    this.video.addEventListener('ratechange', this.handleRateChange);
    this.video.addEventListener('ended', this.handleEnded);
  }

  removeVideoListeners() {
    if (!this.video) return;

    this.video.removeEventListener('play', this.handlePlay);
    this.video.removeEventListener('pause', this.handlePause);
    this.video.removeEventListener('seeking', this.handleSeeking);
    this.video.removeEventListener('seeked', this.handleSeeked);
    this.video.removeEventListener('ratechange', this.handleRateChange);
    this.video.removeEventListener('ended', this.handleEnded);
  }

  handlePlay = () => {
    console.log('[VideoCapture] Video play');
    this.sendStatus('play');
  };

  handlePause = () => {
    console.log('[VideoCapture] Video pause');
    this.sendStatus('pause');
  };

  handleSeeking = () => {
    console.log('[VideoCapture] Video seeking');
    this.sendStatus('seeking');
  };

  handleSeeked = () => {
    console.log('[VideoCapture] Video seeked to', this.video.currentTime);
    this.sendStatus('seeked');
  };

  handleRateChange = () => {
    console.log('[VideoCapture] Playback rate changed to', this.video.playbackRate);
    this.sendStatus('ratechange');
  };

  handleEnded = () => {
    console.log('[VideoCapture] Video ended');
    this.sendStatus('ended');
  };

  startPolling() {
    this.stopPolling();
    this.pollInterval = setInterval(() => {
      this.sendStatus();
    }, CONFIG.STATUS_POLL_INTERVAL);
  }

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  getStatus() {
    if (!this.video) {
      return null;
    }

    return {
      currentTime: this.video.currentTime,
      paused: this.video.paused,
      playbackRate: this.video.playbackRate,
      duration: this.video.duration,
      ended: this.video.ended,
    };
  }

  sendStatus(event = 'poll') {
    const status = this.getStatus();
    if (!status) return;

    // Avoid sending duplicate statuses during polling
    if (event === 'poll' && this.lastStatus) {
      if (
        Math.abs(status.currentTime - this.lastStatus.currentTime) < 0.1 &&
        status.paused === this.lastStatus.paused &&
        status.playbackRate === this.lastStatus.playbackRate
      ) {
        return;
      }
    }

    this.lastStatus = { ...status };

    this.sendMessage({
      type: MSG.VIDEO_STATUS,
      event,
      ...status,
    });
  }

  sendMessage(message) {
    try {
      chrome.runtime.sendMessage(message);
    } catch (error) {
      console.error('[VideoCapture] Failed to send message:', error);
    }
  }

  setupObserver() {
    this.observer = new MutationObserver((mutations) => {
      // Check if video elements were added or removed
      let shouldCheck = false;

      for (const mutation of mutations) {
        if (mutation.type === 'childList') {
          for (const node of mutation.addedNodes) {
            if (node.nodeName === 'VIDEO' || (node.querySelector && node.querySelector('video'))) {
              shouldCheck = true;
              break;
            }
          }
          for (const node of mutation.removedNodes) {
            if (node === this.video || (node.contains && node.contains(this.video))) {
              shouldCheck = true;
              break;
            }
          }
        }
        if (shouldCheck) break;
      }

      if (shouldCheck) {
        // Debounce the check
        clearTimeout(this.checkTimeout);
        this.checkTimeout = setTimeout(() => this.findVideo(), 100);
      }
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }
}

// Initialize tracker
const tracker = new VideoTracker();
