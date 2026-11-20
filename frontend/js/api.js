/**
 * ============================================================================
 * AI-Powered Natural Language Turing Machine Simulator
 * Module: API Client
 * ============================================================================
 * 
 * Strict Responsibility:
 * All HTTP communication with the Python FastAPI backend resides exclusively
 * inside this module. The UI does not execute TM logic directly.
 * The backend is the single source of truth for machine compilation and execution.
 */

(function (window) {
  'use strict';

  // Storage key for custom backend URL configuration
  const STORAGE_KEY_BACKEND_URL = 'tm_backend_url';
  const DEFAULT_BACKEND_URL = 'http://127.0.0.1:8000';

  /**
   * Retrieves the configured backend base URL.
   * Falls back to http://127.0.0.1:8000 if not customized.
   * @returns {string}
   */
  function getBaseUrl() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_BACKEND_URL);
      if (stored && typeof stored === 'string' && stored.trim().length > 0) {
        return stored.trim().replace(/\/+$/, ''); // Remove trailing slashes
      }
    } catch (e) {
      console.warn('LocalStorage unavailable for backend URL lookup:', e);
    }
    return DEFAULT_BACKEND_URL;
  }

  /**
   * Sets and persists the configured backend base URL.
   * @param {string} url 
   * @returns {string} The normalized URL
   */
  function setBaseUrl(url) {
    let cleanUrl = DEFAULT_BACKEND_URL;
    if (url && typeof url === 'string' && url.trim().length > 0) {
      cleanUrl = url.trim().replace(/\/+$/, '');
    }
    try {
      localStorage.setItem(STORAGE_KEY_BACKEND_URL, cleanUrl);
    } catch (e) {
      console.warn('LocalStorage unavailable for saving backend URL:', e);
    }
    return cleanUrl;
  }

  /**
   * Resets the backend URL to the default value.
   */
  function resetBaseUrl() {
    try {
      localStorage.removeItem(STORAGE_KEY_BACKEND_URL);
    } catch (e) {
      // ignore
    }
    return DEFAULT_BACKEND_URL;
  }

  /**
   * Internal helper for performing fetch calls with timeout and unified error handling.
   * @param {string} endpoint 
   * @param {RequestInit} options 
   * @param {number} timeoutMs 
   * @returns {Promise<any>}
   */
  async function apiFetch(endpoint, options = {}, timeoutMs = 8000) {
    const baseUrl = getBaseUrl();
    const url = `${baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    const headers = {
      'Accept': 'application/json',
      ...(options.headers || {})
    };

    if (options.body && typeof options.body === 'string') {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal
      });
      clearTimeout(timer);

      // Handle non-JSON or HTTP errors
      const contentType = response.headers.get('content-type') || '';
      let data = null;

      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        data = { message: text };
      }

      if (!response.ok) {
        // Build descriptive error object
        const message = (data && (data.detail || (data.error && data.error.message) || data.message)) ||
          `HTTP Error ${response.status}: ${response.statusText}`;
        const error = new Error(message);
        error.status = response.status;
        error.data = data;
        error.code = (data && data.error && data.error.code) || `HTTP_${response.status}`;
        throw error;
      }

      return data;
    } catch (err) {
      clearTimeout(timer);
      if (err.name === 'AbortError') {
        const timeoutError = new Error(`Request to backend timed out after ${timeoutMs}ms (${url})`);
        timeoutError.code = 'TIMEOUT';
        throw timeoutError;
      }
      if (err.message && err.message.toLowerCase().includes('failed to fetch')) {
        const networkError = new Error(
          `Unable to connect to backend at ${baseUrl}. Ensure the FastAPI server is running with 'uvicorn app.main:app --reload'.`
        );
        networkError.code = 'NETWORK_ERROR';
        throw networkError;
      }
      throw err;
    }
  }

  /**
   * Health Check: Verifies connection to the backend.
   * GET /api/health
   * @returns {Promise<{ ok: boolean, status?: string, error?: string }>}
   */
  async function checkHealth() {
    try {
      const data = await apiFetch('/api/health', { method: 'GET' }, 3500);
      return {
        ok: true,
        status: data && data.status ? data.status : 'ok',
        url: getBaseUrl()
      };
    } catch (err) {
      return {
        ok: false,
        error: err.message,
        code: err.code || 'UNKNOWN',
        url: getBaseUrl()
      };
    }
  }

  /**
   * Normalizes alphabet input to array of unique string symbols.
   * Handles string format like "0, 1" or ["0", "1"].
   * @param {string|string[]} alphabetInput 
   * @returns {string[]}
   */
  function normalizeAlphabet(alphabetInput) {
    if (Array.isArray(alphabetInput)) {
      return alphabetInput.map(s => String(s).trim()).filter(Boolean);
    }
    if (typeof alphabetInput === 'string') {
      return alphabetInput
        .split(/[,\s]+/)
        .map(s => s.trim())
        .filter(s => s.length > 0);
    }
    return ['0', '1'];
  }

  /**
   * Generate Machine: Sends natural language condition to compile the TM.
   * POST /api/machine/generate
   * 
   * @param {string} condition - Natural language description
   * @param {string|string[]} alphabet - Alphabet symbols
   * @returns {Promise<{ success: boolean, machine?: object, condition?: object, rules_text?: string, rag_sources?: array, error?: object }>}
   */
  async function generateMachine(condition, alphabet = ['0', '1']) {
    if (!condition || !condition.trim()) {
      throw new Error('Condition cannot be empty.');
    }

    const payload = {
      condition: condition.trim(),
      alphabet: normalizeAlphabet(alphabet)
    };

    const response = await apiFetch('/api/machine/generate', {
      method: 'POST',
      body: JSON.stringify(payload)
    }, 12000);

    return response;
  }

  /**
   * Run Machine: Executes simulation on the backend.
   * POST /api/machine/run
   * 
   * @param {string} condition - Natural language description
   * @param {string} inputString - Input tape string to test
   * @param {string|string[]} alphabet - Alphabet symbols
   * @param {number} maxSteps - Step guard limit
   * @returns {Promise<object>} Simulation response including trace and final status
   */
  async function runMachine(condition, inputString = '', alphabet = ['0', '1'], maxSteps = 1000) {
    if (!condition || !condition.trim()) {
      throw new Error('Condition cannot be empty.');
    }

    const payload = {
      condition: condition.trim(),
      input_string: inputString !== undefined && inputString !== null ? String(inputString) : '',
      alphabet: normalizeAlphabet(alphabet),
      max_steps: Number(maxSteps) || 1000
    };

    const response = await apiFetch('/api/machine/run', {
      method: 'POST',
      body: JSON.stringify(payload)
    }, 15000);

    // Validate that response contains required structure
    if (!response || typeof response !== 'object') {
      throw new Error('Invalid backend response: expected a JSON response object.');
    }

    // If simulation was successful, validate and normalize each trace step
    if (response.success && Array.isArray(response.trace)) {
      if (response.trace.length === 0 && (response.status === 'ACCEPT' || response.status === 'REJECT')) {
        throw new Error('Backend returned an empty execution trace for a completed simulation.');
      }
      response.trace = response.trace.map(validateAndNormalizeTraceStep);
    } else if (response.success && !Array.isArray(response.trace)) {
      throw new Error('Simulation response is missing the required execution trace array.');
    }

    return response;
  }

  /**
   * Strictly validates and normalizes a trace step from the backend.
   * Rejects malformed records instead of fabricating default configurations.
   * 
   * @param {object} step - Raw trace record from backend
   * @param {number} index - Trace step index
   * @returns {object} Validated, normalized trace step
   * @throws {Error} If the trace record is malformed
   */
  function validateAndNormalizeTraceStep(step, index) {
    if (!step || typeof step !== 'object') {
      throw new Error(`Trace record at step ${index} is malformed: expected a configuration object.`);
    }

    // 1. Validate State
    const state = step.current_state !== undefined ? step.current_state : step.state;
    if (state === undefined || state === null || String(state).trim() === '') {
      throw new Error(`Trace record at step ${index} is missing a valid state identifier.`);
    }

    // 2. Validate Head Position (must be a valid integer, can be negative)
    const rawHead = step.head_position !== undefined ? step.head_position : step.head;
    if (rawHead === undefined || rawHead === null || isNaN(Number(rawHead))) {
      throw new Error(`Trace record at step ${index} is missing a valid numeric head position.`);
    }
    const head = Number(rawHead);

    // 3. Validate Tape
    if (step.tape === undefined || step.tape === null) {
      throw new Error(`Trace record at step ${index} is missing tape configuration.`);
    }

    // Normalize tape representation (supports Array, String, or Indexed Object)
    let tape = [];
    const tapeOffset = step.tape_offset !== undefined ? Number(step.tape_offset) : (step.start_index !== undefined ? Number(step.start_index) : 0);

    if (Array.isArray(step.tape)) {
      tape = step.tape.map(s => (s === null || s === undefined ? 'B' : String(s)));
    } else if (typeof step.tape === 'string') {
      tape = step.tape.split('');
    } else if (typeof step.tape === 'object') {
      tape = { ...step.tape };
    } else {
      throw new Error(`Trace record at step ${index} has unsupported tape type: ${typeof step.tape}.`);
    }

    const stepNum = step.step !== undefined && !isNaN(Number(step.step)) ? Number(step.step) : index;
    const read = step.read_symbol !== undefined ? step.read_symbol : (step.read !== undefined ? step.read : '');
    const write = step.write_symbol !== undefined ? step.write_symbol : (step.write !== undefined ? step.write : null);
    const move = step.direction !== undefined ? step.direction : (step.move !== undefined ? step.move : null);
    const nextState = step.next_state !== undefined ? step.next_state : null;

    return {
      step: stepNum,
      state: String(state),
      current_state: String(state),
      head,
      head_position: head,
      read: read !== null && read !== undefined ? String(read) : '',
      read_symbol: read !== null && read !== undefined ? String(read) : '',
      write: write !== null && write !== undefined ? String(write) : null,
      write_symbol: write !== null && write !== undefined ? String(write) : null,
      move: move !== null && move !== undefined ? String(move) : null,
      direction: move !== null && move !== undefined ? String(move) : null,
      next_state: nextState !== null && nextState !== undefined ? String(nextState) : null,
      tape,
      tape_offset: tapeOffset
    };
  }

  // Public Namespace Export
  window.TMApi = {
    DEFAULT_BACKEND_URL,
    getBaseUrl,
    setBaseUrl,
    resetBaseUrl,
    checkHealth,
    generateMachine,
    runMachine,
    normalizeAlphabet,
    validateAndNormalizeTraceStep
  };

})(window);
