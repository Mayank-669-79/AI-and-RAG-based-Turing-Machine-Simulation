/**
 * ============================================================================
 * AI-Powered Natural Language Turing Machine Simulator
 * Module: Visualization & Rendering
 * ============================================================================
 * 
 * Strict Responsibility:
 * Renders all non-tape DOM panels using data received from the backend:
 * - Machine 7-Tuple & Formal Specification
 * - Transition Rules Table
 * - Execution Trace / Transition History Table
 * - Results Outcome Card (ACCEPT / REJECT / STEP_LIMIT / NEEDS_CLARIFICATION)
 * - RAG Knowledge Base References
 * 
 * Never fabricates transitions, execution traces, or accept/reject decisions.
 */

(function (window) {
  'use strict';

  /**
   * Safe HTML escaping helper to prevent XSS.
   * @param {string} str 
   * @returns {string}
   */
  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Helper to format array of symbols/states into curly set notation {a, b, c}.
   * @param {string[]} arr 
   * @returns {string}
   */
  function formatSet(arr) {
    if (!arr || !Array.isArray(arr) || arr.length === 0) return '∅';
    return `{ ${arr.map(escapeHtml).join(', ')} }`;
  }

  /**
   * Renders the formal machine specifications into the Machine Info Panel.
   * @param {object} machine - Backend machine definition
   * @param {HTMLElement} container - DOM container
   */
  function renderMachineInfo(machine, container) {
    if (!container) return;

    if (!machine || typeof machine !== 'object') {
      container.innerHTML = `
        <div class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="4" width="20" height="16" rx="2"></rect>
            <path d="M10 4v4"></path>
            <path d="M2 8h20"></path>
          </svg>
          <p>No Turing Machine generated yet.<br>Enter a natural language condition and click "Generate Machine".</p>
        </div>
      `;
      return;
    }

    const startState = machine.start_state || 'q0';
    const acceptStates = machine.accept_states || ['q_accept'];
    const rejectStates = machine.reject_states || ['q_reject'];
    const inputAlphabet = machine.input_alphabet || ['0', '1'];
    const tapeAlphabet = machine.tape_alphabet || ['0', '1', 'B'];
    const blankSymbol = machine.blank_symbol || 'B';
    const transitions = machine.transitions || [];

    let html = `
      <div class="machine-tuple-grid">
        <div class="tuple-item">
          <span class="tuple-label">Start State (q₀)</span>
          <span class="tuple-value">${escapeHtml(startState)}</span>
        </div>
        <div class="tuple-item">
          <span class="tuple-label">Accept States (F_acc)</span>
          <span class="tuple-value">${formatSet(acceptStates)}</span>
        </div>
        <div class="tuple-item">
          <span class="tuple-label">Reject States (F_rej)</span>
          <span class="tuple-value">${formatSet(rejectStates)}</span>
        </div>
        <div class="tuple-item">
          <span class="tuple-label">Input Alphabet (Σ)</span>
          <span class="tuple-value">${formatSet(inputAlphabet)}</span>
        </div>
        <div class="tuple-item">
          <span class="tuple-label">Tape Alphabet (Γ)</span>
          <span class="tuple-value">${formatSet(tapeAlphabet)}</span>
        </div>
        <div class="tuple-item">
          <span class="tuple-label">Blank Symbol (⊔)</span>
          <span class="tuple-value">${escapeHtml(blankSymbol)}</span>
        </div>
      </div>

      <div style="margin-top: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <span style="font-size: 0.72rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase;">
            Transition Rules Table (${transitions.length} total)
          </span>
        </div>
        <div class="table-scroll-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Current State</th>
                <th>Read</th>
                <th>Next State</th>
                <th>Write</th>
                <th>Direction</th>
              </tr>
            </thead>
            <tbody>
    `;

    if (transitions.length === 0) {
      html += `<tr><td colspan="5" style="text-align: center; color: var(--text-dim);">No transitions defined.</td></tr>`;
    } else {
      transitions.forEach(tr => {
        const curr = tr.current_state || tr.state || '';
        const read = tr.read_symbol !== undefined ? tr.read_symbol : (tr.read !== undefined ? tr.read : '');
        const next = tr.next_state || '';
        const write = tr.write_symbol !== undefined ? tr.write_symbol : (tr.write !== undefined ? tr.write : '');
        const dir = tr.direction || tr.move || 'S';

        html += `
          <tr>
            <td><strong>${escapeHtml(curr)}</strong></td>
            <td><code style="color: var(--accent-sky);">${escapeHtml(read)}</code></td>
            <td><strong>${escapeHtml(next)}</strong></td>
            <td><code style="color: var(--accent-emerald);">${escapeHtml(write)}</code></td>
            <td><span class="dir-pill ${escapeHtml(dir)}">${escapeHtml(dir)}</span></td>
          </tr>
        `;
      });
    }

    html += `
            </tbody>
          </table>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  /**
   * Renders the Transition History table from the simulation trace.
   * @param {object[]} trace - Array of normalized trace steps
   * @param {number} activeStepIndex - Currently active step
   * @param {HTMLElement} container - DOM container
   * @param {Function} onStepSelect - Callback when user clicks a row
   */
  function renderTransitionHistory(trace, activeStepIndex = 0, container, onStepSelect) {
    if (!container) return;

    if (!trace || !Array.isArray(trace) || trace.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          <p>No execution trace available yet.<br>Click "Run Simulation" or "Step" to execute.</p>
        </div>
      `;
      return;
    }

    let html = `
      <div class="table-scroll-container" id="history-scroll-box" style="max-height: 280px;">
        <table class="data-table" id="history-table">
          <thead>
            <tr>
              <th>Step</th>
              <th>Current State</th>
              <th>Read</th>
              <th>Write</th>
              <th>Dir</th>
              <th>Next State</th>
              <th>Head Pos</th>
            </tr>
          </thead>
          <tbody>
    `;

    trace.forEach((step, idx) => {
      const isActive = idx === activeStepIndex;
      const isInitial = idx === 0 && (step.write === null || step.write === undefined);

      html += `
        <tr class="trace-row ${isActive ? 'active-trace-row' : ''}" data-step-index="${idx}" style="cursor: pointer;">
          <td>#${step.step !== undefined ? step.step : idx}</td>
          <td><strong>${escapeHtml(step.state)}</strong></td>
          <td>${isInitial ? '<span style="color:var(--text-dim);">Init</span>' : `<code style="color:var(--accent-sky);">${escapeHtml(step.read)}</code>`}</td>
          <td>${isInitial ? '<span style="color:var(--text-dim);">-</span>' : `<code style="color:var(--accent-emerald);">${escapeHtml(step.write)}</code>`}</td>
          <td>${isInitial ? '<span style="color:var(--text-dim);">-</span>' : `<span class="dir-pill ${escapeHtml(step.move)}">${escapeHtml(step.move)}</span>`}</td>
          <td>${step.next_state ? `<strong>${escapeHtml(step.next_state)}</strong>` : '<span style="color:var(--text-dim);">-</span>'}</td>
          <td>[${step.head !== undefined ? step.head : 0}]</td>
        </tr>
      `;
    });

    html += `
          </tbody>
        </table>
      </div>
    `;

    container.innerHTML = html;

    // Attach row click listeners for jumping directly to step
    const rows = container.querySelectorAll('.trace-row');
    rows.forEach(row => {
      row.addEventListener('click', () => {
        const stepIdx = parseInt(row.getAttribute('data-step-index'), 10);
        if (!isNaN(stepIdx) && typeof onStepSelect === 'function') {
          onStepSelect(stepIdx);
        }
      });
    });

    // Ensure active row is scrolled into view
    scrollToActiveHistoryRow(container);
  }

  /**
   * Fast update of the active history table row without full re-render.
   * @param {number} activeStepIndex 
   * @param {HTMLElement} container 
   */
  function updateActiveHistoryRow(activeStepIndex, container) {
    if (!container) return;

    const rows = container.querySelectorAll('.trace-row');
    rows.forEach((row, idx) => {
      if (idx === activeStepIndex) {
        row.classList.add('active-trace-row');
      } else {
        row.classList.remove('active-trace-row');
      }
    });

    scrollToActiveHistoryRow(container);
  }

  /**
   * Auto-scrolls the active trace row into view inside the history table.
   * @param {HTMLElement} container 
   */
  function scrollToActiveHistoryRow(container) {
    const scrollBox = container.querySelector('#history-scroll-box');
    const activeRow = container.querySelector('.active-trace-row');
    if (scrollBox && activeRow) {
      const boxRect = scrollBox.getBoundingClientRect();
      const rowRect = activeRow.getBoundingClientRect();

      if (rowRect.top < boxRect.top || rowRect.bottom > boxRect.bottom) {
        activeRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }

  /**
   * Renders the Results Outcome panel with status badge and execution metrics.
   * Supports: ACCEPT, REJECT, STEP_LIMIT, INVALID_MACHINE, INVALID_CONDITION, AMBIGUOUS_CONDITION, NEEDS_CLARIFICATION.
   * 
   * @param {object} result - Simulation result or error info from backend
   * @param {HTMLElement} container - DOM container
   */
  function renderResult(result, container) {
    if (!container) return;

    if (!result || typeof result !== 'object') {
      container.innerHTML = `
        <div class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 14 14"></polyline>
          </svg>
          <p>Ready for simulation.<br>Run the machine to view ACCEPT, REJECT, or STEP_LIMIT results.</p>
        </div>
      `;
      return;
    }

    const status = result.status || (result.code) || (result.success ? 'COMPLETED' : 'ERROR');
    const reason = result.reason || (result.error && result.error.code) || 'Execution completed';
    const steps = result.steps !== undefined ? result.steps : (result.trace ? result.trace.length : 0);
    const finalState = result.final_state || 'N/A';
    const headPos = result.head_position !== undefined ? result.head_position : 0;
    const explanation = result.explanation || (result.error && result.error.message) || result.message || 'Machine execution completed.';

    // Status icon mapping
    let iconSvg = '';
    if (status === 'ACCEPT') {
      iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
    } else if (status === 'REJECT') {
      iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
    } else {
      iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
    }

    container.innerHTML = `
      <div class="result-banner-box status-${escapeHtml(status)}">
        <div>
          <span style="font-size: 0.68rem; text-transform: uppercase; color: var(--text-dim); font-weight: 600; display: block; margin-bottom: 2px;">
            Deterministic Simulation Decision
          </span>
          <div class="status-badge">
            ${iconSvg}
            <span>${escapeHtml(status)}</span>
          </div>
        </div>
        <div style="text-align: right;">
          <span style="font-size: 0.68rem; text-transform: uppercase; color: var(--text-dim); font-weight: 600; display: block;">
            Halt Reason
          </span>
          <span style="font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-main); font-weight: 600;">
            ${escapeHtml(reason)}
          </span>
        </div>
      </div>

      <div class="result-explanation">
        <strong style="color: var(--text-main);">Explanation:</strong> ${escapeHtml(explanation)}
      </div>

      <div class="result-stats-row">
        <div class="stat-pill">
          <span class="stat-label">Total Steps</span>
          <span class="stat-val">${escapeHtml(steps)}</span>
        </div>
        <div class="stat-pill">
          <span class="stat-label">Final State</span>
          <span class="stat-val" style="color: var(--accent-sky);">${escapeHtml(finalState)}</span>
        </div>
        <div class="stat-pill">
          <span class="stat-label">Final Head Pos</span>
          <span class="stat-val">[${escapeHtml(headPos)}]</span>
        </div>
      </div>
    `;
  }

  /**
   * Renders retrieved RAG Automata Knowledge Base references.
   * @param {object[]} ragSources - Retrieved source chunks
   * @param {HTMLElement} container - DOM container
   */
  function renderRagSources(ragSources, container) {
    if (!container) return;

    if (!ragSources || !Array.isArray(ragSources) || ragSources.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
          </svg>
          <p>No RAG reference notes retrieved yet.<br>Sources from <code>rag_pipeline/knowledge_base</code> will appear after generating or running a machine.</p>
        </div>
      `;
      return;
    }

    let html = `
      <div class="rag-disclaimer">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        <span>
          <strong>Automata Theory Reference:</strong> Retrieved knowledge guides formal machine compilation. Deterministic simulation execution is verified independently by the Python TM engine.
        </span>
      </div>
      <div class="rag-sources-list">
    `;

    ragSources.forEach((src) => {
      const sourceName = src.source || src.filename || 'knowledge_base.md';
      const topic = src.topic || 'Automata Construction Pattern';
      const score = src.score !== undefined ? `${(Number(src.score) * 100).toFixed(0)}% Match` : (src.distance !== undefined ? `Dist: ${Number(src.distance).toFixed(2)}` : null);
      const content = src.content || src.text || 'Knowledge chunk context retrieved from ChromaDB.';

      html += `
        <div class="rag-source-card">
          <div class="rag-source-header">
            <span class="rag-source-file">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              ${escapeHtml(sourceName)}
            </span>
            ${score ? `<span class="rag-source-score">${escapeHtml(score)}</span>` : ''}
          </div>
          <div class="rag-source-topic">${escapeHtml(topic)}</div>
          <div class="rag-source-content">${escapeHtml(content)}</div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  }

  // Public Namespace Export
  window.TMViz = {
    renderMachineInfo,
    renderTransitionHistory,
    updateActiveHistoryRow,
    renderResult,
    renderRagSources
  };

})(window);
