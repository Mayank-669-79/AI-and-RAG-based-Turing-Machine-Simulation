/**
 * ============================================================================
 * AI-Powered Natural Language Turing Machine Simulator
 * Module: Tape Visualization
 * ============================================================================
 * 
 * Strict Responsibility:
 * Renders the Turing Machine tape, individual cells, symbols, and read/write
 * head position strictly from trace data returned by the backend.
 * Supports negative head indices, infinite tape expansion with blank cells,
 * and smooth viewport tracking.
 */

(function (window) {
  'use strict';

  // Constants
  const BLANK_SYMBOL = 'B';
  const DEFAULT_PADDING_CELLS = 5; // Blank cells visible on left & right margins

  /**
   * Tape visualization manager
   */
  class TuringTapeVisualizer {
    constructor() {
      this.container = null;
      this.trackElement = null;
      this.wrapperElement = null;
      this.headMarker = null;

      // Current visualization state
      this.currentTape = [];
      this.currentHead = 0;
      this.currentState = 'q0';
      this.currentOffset = 0;
      this.prevHead = null;
      this.prevTape = [];

      // Auto-centering debounce/animation handle
      this.scrollAnimationFrame = null;
    }

    /**
     * Initializes DOM bindings for the tape component.
     * @param {string|HTMLElement} containerRef 
     */
    init(containerRef) {
      if (typeof containerRef === 'string') {
        this.container = document.getElementById(containerRef);
      } else {
        this.container = containerRef;
      }

      if (!this.container) {
        console.error('TMTape initialization failed: container element not found.');
        return;
      }

      this.wrapperElement = this.container.querySelector('.tape-track-wrapper');
      this.trackElement = this.container.querySelector('.tape-track');
      this.headMarker = this.container.querySelector('.tape-head-marker');

      // Add window resize listener to keep head centered
      window.addEventListener('resize', () => {
        if (this.currentTape.length > 0) {
          this.centerHead(false);
        }
      });
    }

    /**
     * Formats blank symbols for display.
     * @param {string} symbol 
     * @returns {string}
     */
    displaySymbol(symbol) {
      if (symbol === null || symbol === undefined || symbol === '' || symbol === BLANK_SYMBOL) {
        return BLANK_SYMBOL;
      }
      return String(symbol);
    }

    /**
     * Renders a configuration from the backend trace.
     * Handles positive, zero, and negative head positions seamlessly,
     * whether the backend provides tape as an array, array with offset, or indexed dictionary.
     * 
     * @param {string[]|object|string} tapeData - The symbols on the tape
     * @param {number} headPosition - Head index (supports negative values)
     * @param {string} state - Current machine state
     * @param {object} [options] - Additional render options (animate, tapeOffset)
     */
    render(tapeData = [], headPosition = 0, state = 'q0', options = {}) {
      if (!this.trackElement) return;

      const head = Number(headPosition) || 0;
      const offset = options.tapeOffset !== undefined ? Number(options.tapeOffset) : (options.traceStep && options.traceStep.tape_offset ? Number(options.traceStep.tape_offset) : 0);

      this.prevTape = Array.isArray(this.currentTape) ? [...this.currentTape] : { ...this.currentTape };
      this.prevHead = this.currentHead;
      this.currentTape = tapeData;
      this.currentHead = head;
      this.currentState = state || 'q0';
      this.currentOffset = offset;

      // Determine virtual tape bounds and symbol getter
      let minIndex = 0;
      let maxIndex = 0;
      let getSymbolAt = (i) => BLANK_SYMBOL;

      if (Array.isArray(tapeData)) {
        // Tape array where array index k represents virtual tape index (k + offset)
        const tapeLength = tapeData.length;
        const virtualTapeMin = offset;
        const virtualTapeMax = offset + Math.max(0, tapeLength - 1);

        minIndex = Math.min(0, head, virtualTapeMin) - DEFAULT_PADDING_CELLS;
        maxIndex = Math.max(0, head, virtualTapeMax) + DEFAULT_PADDING_CELLS;

        getSymbolAt = (i) => {
          const arrIdx = i - offset;
          if (arrIdx >= 0 && arrIdx < tapeLength) {
            const val = tapeData[arrIdx];
            return (val !== null && val !== undefined && val !== '') ? String(val) : BLANK_SYMBOL;
          }
          return BLANK_SYMBOL;
        };
      } else if (tapeData && typeof tapeData === 'object') {
        // Indexed mapping e.g. { "-2": "1", "-1": "0", "0": "1" }
        const numericKeys = Object.keys(tapeData).map(Number).filter(n => !isNaN(n));
        const keysMin = numericKeys.length > 0 ? Math.min(...numericKeys) : 0;
        const keysMax = numericKeys.length > 0 ? Math.max(...numericKeys) : 0;

        minIndex = Math.min(0, head, keysMin) - DEFAULT_PADDING_CELLS;
        maxIndex = Math.max(0, head, keysMax) + DEFAULT_PADDING_CELLS;

        getSymbolAt = (i) => {
          const val = tapeData[i] !== undefined ? tapeData[i] : tapeData[String(i)];
          return (val !== null && val !== undefined && val !== '') ? String(val) : BLANK_SYMBOL;
        };
      } else if (typeof tapeData === 'string') {
        const chars = tapeData.split('');
        minIndex = Math.min(0, head) - DEFAULT_PADDING_CELLS;
        maxIndex = Math.max(0, head, chars.length - 1) + DEFAULT_PADDING_CELLS;

        getSymbolAt = (i) => {
          if (i >= 0 && i < chars.length) {
            return chars[i];
          }
          return BLANK_SYMBOL;
        };
      }

      // Construct fragment of cells
      const fragment = document.createDocumentFragment();

      for (let i = minIndex; i <= maxIndex; i++) {
        const cell = document.createElement('div');
        cell.className = 'tape-cell';
        cell.setAttribute('data-index', i);

        // Cell index label
        const indexLabel = document.createElement('span');
        indexLabel.className = 'tape-cell-index';
        indexLabel.textContent = `[${i}]`;
        cell.appendChild(indexLabel);

        // Symbol resolution
        const symbolVal = getSymbolAt(i);

        const symbolElement = document.createElement('span');
        symbolElement.className = 'tape-cell-symbol';
        symbolElement.textContent = symbolVal;

        if (symbolVal === BLANK_SYMBOL) {
          cell.classList.add('blank');
        }

        // Active Head styling
        if (i === head) {
          cell.classList.add('active-head');
        }

        // Detect and animate symbol write changes
        if (options.animate && this.prevHead === i) {
          cell.classList.add('written');
        }

        cell.appendChild(symbolElement);
        fragment.appendChild(cell);
      }

      // Update Track DOM
      this.trackElement.innerHTML = '';
      this.trackElement.appendChild(fragment);

      // Update Head Marker text if present
      if (this.headMarker) {
        const labelEl = this.headMarker.querySelector('.tape-head-label');
        if (labelEl) {
          labelEl.textContent = `HEAD : ${this.currentState}`;
        }
      }

      // Center the active cell in view
      this.centerHead(options.smooth !== false);
    }

    /**
     * Centers the active head cell within the scrollable viewport.
     * @param {boolean} smooth 
     */
    centerHead(smooth = true) {
      if (!this.wrapperElement || !this.trackElement) return;

      const activeCell = this.trackElement.querySelector('.tape-cell.active-head');
      if (!activeCell) return;

      if (this.scrollAnimationFrame) {
        cancelAnimationFrame(this.scrollAnimationFrame);
      }

      this.scrollAnimationFrame = requestAnimationFrame(() => {
        const wrapperRect = this.wrapperElement.getBoundingClientRect();
        const activeCellRect = activeCell.getBoundingClientRect();

        const currentScrollLeft = this.wrapperElement.scrollLeft;
        const targetScrollLeft = currentScrollLeft + (activeCellRect.left - wrapperRect.left) - (wrapperRect.width / 2) + (activeCellRect.width / 2);

        this.wrapperElement.scrollTo({
          left: Math.max(0, targetScrollLeft),
          behavior: smooth ? 'smooth' : 'auto'
        });
      });
    }

    /**
     * Resets the tape visualization to default blank cells.
     */
    clear() {
      this.currentTape = [];
      this.currentHead = 0;
      this.currentState = 'q0';
      this.prevHead = null;
      this.prevTape = [];

      if (this.trackElement) {
        this.render(['B'], 0, 'q0', { smooth: false });
      }
    }
  }

  // Create singleton instance
  const visualizer = new TuringTapeVisualizer();

  // Public Namespace Export
  window.TMTape = {
    init: (containerRef) => visualizer.init(containerRef),
    render: (tapeArray, headPos, state, options) => visualizer.render(tapeArray, headPos, state, options),
    centerHead: (smooth) => visualizer.centerHead(smooth),
    clear: () => visualizer.clear(),
    getInstance: () => visualizer
  };

})(window);
