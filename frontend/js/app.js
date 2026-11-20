/**
 * ============================================================================
 * AI-Powered Natural Language Turing Machine Simulator
 * Module: Application Controller
 * ============================================================================
 * 
 * Strict Responsibility:
 * Orchestrates UI state, DOM event listeners, input validation, execution
 * playback controls (Run, Step, Pause, Reset), and API coordination.
 * 
 * The JavaScript frontend does NOT implement a Turing Machine engine.
 * Execution decisions and trace configurations come entirely from the backend.
 */

(function (window, document) {
  'use strict';

  // Application State
  const AppState = {
    backendOnline: false,
    currentMachine: null,
    currentCondition: '',
    currentInputString: '',
    currentAlphabet: ['0', '1'],
    currentTrace: [],
    currentStepIndex: 0,
    isPlaying: false,
    playbackTimer: null,
    stepIntervalMs: 500, // Default 1x speed: 500ms per step
    lastSimulationResult: null
  };

  // Preset Test Scenarios from Academic Specifications
  const PRESET_SCENARIOS = [
    {
      label: 'Ends with 1',
      condition: 'The binary string should end with 1.',
      input: '101',
      alphabet: '0, 1',
      expected: 'ACCEPT'
    },
    {
      label: 'Even 0s',
      condition: 'Accept strings containing an even number of zeros.',
      input: '1010',
      alphabet: '0, 1',
      expected: 'ACCEPT'
    },
    {
      label: 'Contains 101',
      condition: 'Accept strings that contain the substring 101.',
      input: '01010',
      alphabet: '0, 1',
      expected: 'ACCEPT'
    },
    {
      label: 'Starts 1 & Ends 0',
      condition: 'The string must start with 1 and end with 0.',
      input: '100',
      alphabet: '0, 1',
      expected: 'ACCEPT'
    },
    {
      label: 'Even Length',
      condition: 'The length of the binary string should be even.',
      input: '1011',
      alphabet: '0, 1',
      expected: 'ACCEPT'
    },
    {
      label: 'Reject 11',
      condition: 'Reject strings containing 11.',
      input: '1010',
      alphabet: '0, 1',
      expected: 'ACCEPT'
    }
  ];

  // DOM Elements Cache
  let dom = {};

  /**
   * Initializes DOM references on document ready.
   */
  function cacheDomElements() {
    dom = {
      // Header & Status
      statusDot: document.getElementById('status-dot'),
      statusText: document.getElementById('status-text'),
      backendUrlLabel: document.getElementById('backend-url-label'),
      btnSettings: document.getElementById('btn-settings'),
      
      // Alerts
      alertBanner: document.getElementById('alert-banner'),
      alertIcon: document.getElementById('alert-icon'),
      alertTitle: document.getElementById('alert-title'),
      alertMessage: document.getElementById('alert-message'),
      alertClose: document.getElementById('alert-close'),

      // Inputs
      conditionInput: document.getElementById('condition-input'),
      inputString: document.getElementById('input-string'),
      alphabetInput: document.getElementById('alphabet-input'),
      maxStepsInput: document.getElementById('max-steps-input'),
      presetsContainer: document.getElementById('presets-container'),

      // Main Action Buttons
      btnGenerate: document.getElementById('btn-generate'),
      btnRun: document.getElementById('btn-run'),
      btnClear: document.getElementById('btn-clear'),

      // Tape Meta
      tapeContainer: document.getElementById('tape-container'),
      tapeStateBadge: document.getElementById('tape-state-badge'),
      tapeStepBadge: document.getElementById('tape-step-badge'),
      tapeHeadBadge: document.getElementById('tape-head-badge'),
      tapeReadBadge: document.getElementById('tape-read-badge'),

      // Tape Playback Controls
      btnPlayPause: document.getElementById('btn-play-pause'),
      btnStepPrev: document.getElementById('btn-step-prev'),
      btnStepNext: document.getElementById('btn-step-next'),
      btnReset: document.getElementById('btn-reset'),
      stepScrubber: document.getElementById('step-scrubber'),
      scrubberLabel: document.getElementById('scrubber-label'),
      speedSelect: document.getElementById('speed-select'),

      // Panels
      panelResults: document.getElementById('panel-results'),
      panelMachineInfo: document.getElementById('panel-machine-info'),
      panelHistory: document.getElementById('panel-history'),
      panelRag: document.getElementById('panel-rag'),

      // Settings Modal
      modalBackdrop: document.getElementById('settings-modal'),
      inputModalUrl: document.getElementById('input-modal-url'),
      btnSaveUrl: document.getElementById('btn-save-url'),
      btnResetUrl: document.getElementById('btn-reset-url'),
      btnCloseModal: document.getElementById('btn-close-modal')
    };
  }

  /**
   * Application Bootstrapper
   */
  function init() {
    cacheDomElements();

    // Initialize Tape Component
    if (window.TMTape && dom.tapeContainer) {
      window.TMTape.init(dom.tapeContainer);
      window.TMTape.clear();
    }

    // Render Initial Empty States
    if (window.TMViz) {
      window.TMViz.renderMachineInfo(null, dom.panelMachineInfo);
      window.TMViz.renderTransitionHistory([], 0, dom.panelHistory);
      window.TMViz.renderResult(null, dom.panelResults);
      window.TMViz.renderRagSources([], dom.panelRag);
    }

    // Render Preset Chips
    renderPresetChips();

    // Attach Event Listeners
    attachEventListeners();

    // Initial Health Check
    checkBackendHealth();
    setInterval(checkBackendHealth, 10000); // Periodic ping every 10s
  }

  /**
   * Renders clickable preset pills in the UI.
   */
  function renderPresetChips() {
    if (!dom.presetsContainer) return;

    dom.presetsContainer.innerHTML = '';
    const label = document.createElement('span');
    label.className = 'presets-label';
    label.textContent = 'Examples:';
    dom.presetsContainer.appendChild(label);

    PRESET_SCENARIOS.forEach((preset) => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'preset-chip';
      chip.textContent = preset.label;
      chip.title = `${preset.condition} (Input: "${preset.input}")`;

      chip.addEventListener('click', () => {
        dom.conditionInput.value = preset.condition;
        dom.inputString.value = preset.input;
        dom.alphabetInput.value = preset.alphabet;

        // Highlight selected chip
        dom.presetsContainer.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');

        showAlert('info', 'Example Loaded', `Loaded scenario: "${preset.condition}" with test input "${preset.input}". Click "Run Simulation" or "Generate Machine".`);
      });

      dom.presetsContainer.appendChild(chip);
    });
  }

  /**
   * Binds UI event listeners.
   */
  function attachEventListeners() {
    // Generate Machine
    dom.btnGenerate.addEventListener('click', handleGenerateMachine);

    // Run Simulation
    dom.btnRun.addEventListener('click', handleRunSimulation);

    // Clear Form
    dom.btnClear.addEventListener('click', handleClearForm);

    // Playback Controls
    dom.btnPlayPause.addEventListener('click', togglePlayPause);
    dom.btnStepNext.addEventListener('click', stepForward);
    dom.btnStepPrev.addEventListener('click', stepBackward);
    dom.btnReset.addEventListener('click', resetSimulation);

    // Step Scrubber Slider
    dom.stepScrubber.addEventListener('input', (e) => {
      const stepIdx = parseInt(e.target.value, 10);
      if (!isNaN(stepIdx)) {
        jumpToStep(stepIdx);
      }
    });

    // Playback Speed Selector
    dom.speedSelect.addEventListener('change', (e) => {
      AppState.stepIntervalMs = parseInt(e.target.value, 10) || 500;
      if (AppState.isPlaying) {
        pausePlayback();
        startPlayback();
      }
    });

    // Alert Banner Close
    dom.alertClose.addEventListener('click', hideAlert);

    // Settings Modal
    dom.btnSettings.addEventListener('click', openSettingsModal);
    dom.btnCloseModal.addEventListener('click', closeSettingsModal);
    dom.btnSaveUrl.addEventListener('click', saveBackendUrl);
    dom.btnResetUrl.addEventListener('click', resetBackendUrlToDefault);
  }

  /* --------------------------------------------------------------------------
     Alert Banner Utility
     -------------------------------------------------------------------------- */
  function showAlert(type, title, message) {
    if (!dom.alertBanner) return;

    dom.alertBanner.className = `alert-banner ${type} show`;
    dom.alertTitle.textContent = title;
    dom.alertMessage.textContent = message;
  }

  function hideAlert() {
    if (dom.alertBanner) {
      dom.alertBanner.className = 'alert-banner';
    }
  }

  /* --------------------------------------------------------------------------
     Backend Health Check
     -------------------------------------------------------------------------- */
  async function checkBackendHealth() {
    if (!window.TMApi) return;

    const currentUrl = window.TMApi.getBaseUrl();
    if (dom.backendUrlLabel) {
      dom.backendUrlLabel.textContent = currentUrl;
    }

    if (dom.statusDot) {
      dom.statusDot.className = 'status-dot checking';
    }
    if (dom.statusText) {
      dom.statusText.textContent = 'Checking...';
    }

    const health = await window.TMApi.checkHealth();
    AppState.backendOnline = health.ok;

    if (health.ok) {
      if (dom.statusDot) dom.statusDot.className = 'status-dot online';
      if (dom.statusText) dom.statusText.textContent = 'Connected';
    } else {
      if (dom.statusDot) dom.statusDot.className = 'status-dot offline';
      if (dom.statusText) dom.statusText.textContent = 'Offline';
    }
  }

  /* --------------------------------------------------------------------------
     Machine Generation Flow
     -------------------------------------------------------------------------- */
  async function handleGenerateMachine() {
    const condition = dom.conditionInput.value.trim();
    const alphabet = dom.alphabetInput.value.trim();

    if (!condition) {
      showAlert('warning', 'Missing Condition', 'Please enter a natural language condition (e.g., "The binary string should end with 1.").');
      dom.conditionInput.focus();
      return;
    }

    pausePlayback();
    setGeneratingState(true);
    hideAlert();

    try {
      const response = await window.TMApi.generateMachine(condition, alphabet);

      // 1. Strict check: failure flag (unsuccessful responses must never show success)
      if (response.success !== true) {
        const err = response.error || {};
        const errMsg = err.message || response.message || response.detail || 'Unable to compile Turing Machine for this condition.';
        const errCode = err.code || response.code || 'GENERATION_ERROR';

        showAlert('error', `Generation Failed (${errCode})`, errMsg);

        if (response.clarification_question || (response.condition && response.condition.clarification_question)) {
          showAlert('warning', 'Clarification Required', response.clarification_question || response.condition.clarification_question);
        }

        AppState.currentMachine = null;
        window.TMViz.renderMachineInfo(null, dom.panelMachineInfo);
        return;
      }

      // 2. Clarification flag check
      if (response.condition && response.condition.needs_clarification) {
        AppState.currentMachine = null;
        window.TMViz.renderMachineInfo(null, dom.panelMachineInfo);
        showAlert('warning', 'Ambiguous Condition', response.condition.clarification_question || 'Backend requested clarification for this condition. Please refine the description.');
        return;
      }

      // 3. Machine validity check
      if (!response.machine || typeof response.machine !== 'object' || !Array.isArray(response.machine.transitions)) {
        AppState.currentMachine = null;
        window.TMViz.renderMachineInfo(null, dom.panelMachineInfo);
        showAlert('error', 'Invalid Machine Definition', 'Backend reported success but returned an incomplete or missing machine specification.');
        return;
      }

      // 4. Valid compilation success
      AppState.currentMachine = response.machine;
      AppState.currentCondition = condition;
      AppState.currentAlphabet = window.TMApi.normalizeAlphabet(alphabet);

      window.TMViz.renderMachineInfo(response.machine, dom.panelMachineInfo);
      window.TMViz.renderRagSources(response.rag_sources || [], dom.panelRag);

      const family = (response.condition && response.condition.family) || 'formal';
      showAlert('success', 'Machine Compiled', `Turing Machine successfully compiled for condition family: "${family}" (${response.machine.transitions.length} transitions).`);

    } catch (err) {
      console.error('Generate Machine Error:', err);
      AppState.currentMachine = null;
      window.TMViz.renderMachineInfo(null, dom.panelMachineInfo);
      showAlert('error', 'Compilation Error', err.message);
    } finally {
      setGeneratingState(false);
    }
  }

  function setGeneratingState(isGenerating) {
    if (!dom.btnGenerate) return;
    dom.btnGenerate.disabled = isGenerating;
    if (isGenerating) {
      dom.btnGenerate.innerHTML = `
        <svg class="spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
          <path d="M12 2a10 10 0 0 1 10 10"></path>
        </svg>
        <span>Compiling...</span>
      `;
    } else {
      dom.btnGenerate.innerHTML = `
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="3" width="20" height="14" rx="2"></rect>
          <line x1="8" y1="21" x2="16" y2="21"></line>
          <line x1="12" y1="17" x2="12" y2="21"></line>
        </svg>
        <span>Generate Machine</span>
      `;
    }
  }

  /* --------------------------------------------------------------------------
     Simulation Run Flow
     -------------------------------------------------------------------------- */
  async function handleRunSimulation() {
    const condition = dom.conditionInput.value.trim();
    const inputString = dom.inputString.value; // May be empty string (valid epsilon in formal languages)
    const alphabet = dom.alphabetInput.value.trim();
    const maxSteps = parseInt(dom.maxStepsInput.value, 10) || 1000;

    if (!condition) {
      showAlert('warning', 'Missing Condition', 'Please enter a natural language condition before running.');
      dom.conditionInput.focus();
      return;
    }

    pausePlayback();
    setRunningState(true);
    hideAlert();

    try {
      const response = await window.TMApi.runMachine(condition, inputString, alphabet, maxSteps);

      // 1. Strict check: failure or error response
      if (response.success !== true) {
        const err = response.error || {};
        const errMsg = err.message || response.message || response.detail || 'Simulation could not be executed.';
        const errCode = err.code || response.code || 'SIMULATION_ERROR';

        // Clear any stale execution state
        AppState.currentTrace = [];
        AppState.lastSimulationResult = null;
        if (window.TMTape) window.TMTape.clear();
        dom.stepScrubber.value = 0;
        dom.stepScrubber.disabled = true;
        updateScrubberLabel(0, 0);

        // Render the error/clarification result directly in the results panel
        window.TMViz.renderResult({
          status: errCode,
          reason: errMsg,
          explanation: response.clarification_question || err.details || errMsg,
          steps: 0,
          final_state: 'N/A',
          head_position: 0
        }, dom.panelResults);

        if (errCode === 'AMBIGUOUS_CONDITION' || errCode === 'UNSUPPORTED_CONDITION' || response.clarification_question) {
          showAlert('warning', 'Clarification Required', response.clarification_question || errMsg);
        } else {
          showAlert('error', `Simulation Failed (${errCode})`, errMsg);
        }
        return;
      }

      // 2. Check for clarification flag in successful envelope
      if (response.condition && response.condition.needs_clarification) {
        AppState.currentTrace = [];
        AppState.lastSimulationResult = null;
        if (window.TMTape) window.TMTape.clear();
        dom.stepScrubber.value = 0;
        dom.stepScrubber.disabled = true;
        updateScrubberLabel(0, 0);

        const q = response.condition.clarification_question || 'Condition is ambiguous and requires clarification.';
        showAlert('warning', 'Clarification Required', q);
        window.TMViz.renderResult({
          status: 'NEEDS_CLARIFICATION',
          reason: 'ambiguous_condition',
          explanation: q,
          steps: 0,
          final_state: 'N/A',
          head_position: 0
        }, dom.panelResults);
        return;
      }

      // 3. Store verified simulation state
      AppState.currentCondition = condition;
      AppState.currentInputString = inputString;
      AppState.currentAlphabet = window.TMApi.normalizeAlphabet(alphabet);
      AppState.currentTrace = response.trace || [];
      AppState.currentStepIndex = 0;
      AppState.lastSimulationResult = response;

      // Update Machine Info and RAG references if provided in run response
      if (response.machine) {
        AppState.currentMachine = response.machine;
        window.TMViz.renderMachineInfo(response.machine, dom.panelMachineInfo);
      }
      if (response.rag_sources) {
        window.TMViz.renderRagSources(response.rag_sources, dom.panelRag);
      }

      // Render Transition History Table with click listener
      window.TMViz.renderTransitionHistory(AppState.currentTrace, 0, dom.panelHistory, (clickedStep) => {
        pausePlayback();
        jumpToStep(clickedStep);
      });

      // Update Scrubber Bounds
      const totalSteps = AppState.currentTrace.length;
      if (totalSteps > 0) {
        dom.stepScrubber.max = totalSteps - 1;
        dom.stepScrubber.value = 0;
        dom.stepScrubber.disabled = false;
        updateScrubberLabel(0, totalSteps - 1);
      } else {
        dom.stepScrubber.disabled = true;
      }

      // Render Initial Configuration on Tape
      if (totalSteps > 0) {
        renderStepConfiguration(0, false);
        // Auto-play the returned execution trace
        startPlayback();
      } else {
        showAlert('warning', 'Empty Trace', 'Backend returned an empty execution trace.');
      }

    } catch (err) {
      console.error('Run Simulation Error:', err);
      AppState.currentTrace = [];
      AppState.lastSimulationResult = null;
      if (window.TMTape) window.TMTape.clear();
      dom.stepScrubber.value = 0;
      dom.stepScrubber.disabled = true;
      updateScrubberLabel(0, 0);

      showAlert('error', 'Execution Error', err.message);
    } finally {
      setRunningState(false);
    }
  }

  function setRunningState(isRunning) {
    if (!dom.btnRun) return;
    dom.btnRun.disabled = isRunning;
    if (isRunning) {
      dom.btnRun.innerHTML = `
        <svg class="spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
          <path d="M12 2a10 10 0 0 1 10 10"></path>
        </svg>
        <span>Simulating...</span>
      `;
    } else {
      dom.btnRun.innerHTML = `
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Run Simulation</span>
      `;
    }
  }

  /* --------------------------------------------------------------------------
     Tape Step Rendering & Playback Engine
     -------------------------------------------------------------------------- */
  function renderStepConfiguration(stepIndex, animate = true) {
    if (!AppState.currentTrace || AppState.currentTrace.length === 0) return;
    if (stepIndex < 0 || stepIndex >= AppState.currentTrace.length) return;

    AppState.currentStepIndex = stepIndex;
    const config = AppState.currentTrace[stepIndex];

    // Render Tape with proper options and offsets
    if (window.TMTape) {
      window.TMTape.render(config.tape, config.head, config.state, {
        animate,
        tapeOffset: config.tape_offset,
        traceStep: config
      });
    }

    // Update Meta Badges
    if (dom.tapeStateBadge) dom.tapeStateBadge.textContent = config.state || 'q0';
    if (dom.tapeStepBadge) dom.tapeStepBadge.textContent = `${config.step !== undefined ? config.step : stepIndex} / ${AppState.currentTrace.length - 1}`;
    if (dom.tapeHeadBadge) dom.tapeHeadBadge.textContent = `[${config.head !== undefined ? config.head : 0}]`;
    if (dom.tapeReadBadge) dom.tapeReadBadge.textContent = config.read !== undefined && config.read !== null && config.read !== '' ? config.read : '-';

    // Update History Highlight
    if (window.TMViz && dom.panelHistory) {
      window.TMViz.updateActiveHistoryRow(stepIndex, dom.panelHistory);
    }

    // Update Scrubber
    if (dom.stepScrubber) {
      dom.stepScrubber.value = stepIndex;
      updateScrubberLabel(stepIndex, AppState.currentTrace.length - 1);
    }

    // Update Prev / Next Button disabled states
    dom.btnStepPrev.disabled = stepIndex <= 0;
    dom.btnStepNext.disabled = stepIndex >= AppState.currentTrace.length - 1;

    // If final step reached, render final result outcome
    if (stepIndex === AppState.currentTrace.length - 1 && AppState.lastSimulationResult) {
      window.TMViz.renderResult(AppState.lastSimulationResult, dom.panelResults);
    }
  }

  function updateScrubberLabel(current, total) {
    if (dom.scrubberLabel) {
      dom.scrubberLabel.textContent = `Step ${current} / ${total}`;
    }
  }

  /* --------------------------------------------------------------------------
     Execution Controls (Run, Pause, Step, Reset)
     -------------------------------------------------------------------------- */
  function togglePlayPause() {
    if (AppState.isPlaying) {
      pausePlayback();
    } else {
      // If at end, loop back to start
      if (AppState.currentStepIndex >= AppState.currentTrace.length - 1) {
        AppState.currentStepIndex = 0;
        renderStepConfiguration(0, false);
      }
      startPlayback();
    }
  }

  function startPlayback() {
    if (!AppState.currentTrace || AppState.currentTrace.length === 0) {
      showAlert('warning', 'No Trace', 'Run a simulation first to generate an execution trace.');
      return;
    }

    AppState.isPlaying = true;
    updatePlayPauseButtonUI(true);

    if (AppState.playbackTimer) clearInterval(AppState.playbackTimer);

    AppState.playbackTimer = setInterval(() => {
      if (AppState.currentStepIndex < AppState.currentTrace.length - 1) {
        renderStepConfiguration(AppState.currentStepIndex + 1, true);
      } else {
        pausePlayback(); // End of trace reached
      }
    }, AppState.stepIntervalMs);
  }

  function pausePlayback() {
    AppState.isPlaying = false;
    if (AppState.playbackTimer) {
      clearInterval(AppState.playbackTimer);
      AppState.playbackTimer = null;
    }
    updatePlayPauseButtonUI(false);
  }

  function updatePlayPauseButtonUI(isPlaying) {
    if (!dom.btnPlayPause) return;
    if (isPlaying) {
      dom.btnPlayPause.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <rect x="6" y="4" width="4" height="16"></rect>
          <rect x="14" y="4" width="4" height="16"></rect>
        </svg>
        <span>Pause</span>
      `;
      dom.btnPlayPause.classList.add('btn-accent');
    } else {
      dom.btnPlayPause.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Play</span>
      `;
      dom.btnPlayPause.classList.remove('btn-accent');
    }
  }

  function stepForward() {
    pausePlayback();
    if (AppState.currentTrace && AppState.currentStepIndex < AppState.currentTrace.length - 1) {
      renderStepConfiguration(AppState.currentStepIndex + 1, true);
    }
  }

  function stepBackward() {
    pausePlayback();
    if (AppState.currentTrace && AppState.currentStepIndex > 0) {
      renderStepConfiguration(AppState.currentStepIndex - 1, false);
    }
  }

  function resetSimulation() {
    pausePlayback();
    if (AppState.currentTrace && AppState.currentTrace.length > 0) {
      renderStepConfiguration(0, false);
    } else {
      if (window.TMTape) window.TMTape.clear();
    }
  }

  function jumpToStep(stepIndex) {
    pausePlayback();
    renderStepConfiguration(stepIndex, false);
  }

  function handleClearForm() {
    pausePlayback();
    dom.conditionInput.value = '';
    dom.inputString.value = '';
    dom.alphabetInput.value = '0, 1';
    dom.maxStepsInput.value = '1000';

    AppState.currentMachine = null;
    AppState.currentTrace = [];
    AppState.currentStepIndex = 0;
    AppState.lastSimulationResult = null;

    if (window.TMTape) window.TMTape.clear();
    if (window.TMViz) {
      window.TMViz.renderMachineInfo(null, dom.panelMachineInfo);
      window.TMViz.renderTransitionHistory([], 0, dom.panelHistory);
      window.TMViz.renderResult(null, dom.panelResults);
      window.TMViz.renderRagSources([], dom.panelRag);
    }

    dom.stepScrubber.value = 0;
    dom.stepScrubber.disabled = true;
    updateScrubberLabel(0, 0);

    hideAlert();
  }

  /* --------------------------------------------------------------------------
     Settings Modal & URL Configuration
     -------------------------------------------------------------------------- */
  function openSettingsModal() {
    if (!dom.modalBackdrop) return;
    dom.inputModalUrl.value = window.TMApi.getBaseUrl();
    dom.modalBackdrop.classList.add('show');
  }

  function closeSettingsModal() {
    if (dom.modalBackdrop) {
      dom.modalBackdrop.classList.remove('show');
    }
  }

  function saveBackendUrl() {
    const newUrl = dom.inputModalUrl.value.trim();
    if (!newUrl) return;

    window.TMApi.setBaseUrl(newUrl);
    closeSettingsModal();
    checkBackendHealth();
    showAlert('info', 'Backend URL Updated', `API endpoint set to: ${newUrl}`);
  }

  function resetBackendUrlToDefault() {
    const defaultUrl = window.TMApi.resetBaseUrl();
    dom.inputModalUrl.value = defaultUrl;
    closeSettingsModal();
    checkBackendHealth();
    showAlert('info', 'Backend URL Reset', `Restored default endpoint: ${defaultUrl}`);
  }

  // Self-initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})(window, document);
