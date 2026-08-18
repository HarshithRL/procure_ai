/**
 * Feedback module — user sentiment / quality feedback on agent responses.
 * 
 * Sprint 1: stub. Collects like/dislike signals for future ML training datasets.
 * 
 * Usage:
 *   feedback.rate(messageId, { liked: true })
 *   feedback.onReady(() => { ... })
 */

(function () {
  'use strict';

  const feedback = window.feedback || {};

  /**
   * Rate a message (like / dislike).
   * @param {string} messageId - Unique message identifier.
   * @param {Object} signal - { liked: boolean, reason?: string }
   */
  feedback.rate = function (messageId, signal) {
    console.debug('[feedback] rated:', messageId, signal);
    // TODO: POST to /api/feedback (Sprint 2)
  };

  /**
   * Emit when the feedback system is ready.
   * @param {Function} callback
   */
  feedback.onReady = function (callback) {
    if (typeof callback === 'function') {
      document.addEventListener('DOMContentLoaded', callback);
      if (document.readyState === 'interactive' || document.readyState === 'complete') {
        callback();
      }
    }
  };

  window.feedback = feedback;
})();
