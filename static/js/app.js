/**
 * FitAI — Main Application JavaScript
 * =====================================
 * Modular, production-ready client-side logic for the FitAI SaaS dashboard.
 * Uses modern ES6+ syntax throughout (const/let, arrow functions, template
 * literals, async/await).  Every public helper is attached to window.FitAI so
 * templates can call them directly when needed.
 */

(() => {
  'use strict';

  /* ------------------------------------------------------------------ */
  /*  CONSTANTS                                                          */
  /* ------------------------------------------------------------------ */

  const FLASH_DISMISS_MS   = 5000;
  const TOAST_DISMISS_MS   = 3000;
  const TYPING_INDICATOR_DELAY = 400;   // min visible time for the dots
  const COUNTER_DURATION_MS    = 1200;
  const PLOTLY_CONFIG = {
    responsive: true,
    displayModeBar: false,
    scrollZoom: false,
  };
  const PLOTLY_DARK_LAYOUT = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor:  'rgba(0,0,0,0)',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    margin: { t: 30, r: 20, b: 40, l: 50 },
    xaxis: { gridcolor: 'rgba(255,255,255,0.06)', zerolinecolor: 'rgba(255,255,255,0.06)' },
    yaxis: { gridcolor: 'rgba(255,255,255,0.06)', zerolinecolor: 'rgba(255,255,255,0.06)' },
    legend: { orientation: 'h', y: -0.15 },
    colorway: ['#7C3AED', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#14B8A6'],
  };

  /* ------------------------------------------------------------------ */
  /*  UTILITY HELPERS                                                    */
  /* ------------------------------------------------------------------ */

  /**
   * Shorthand querySelector / querySelectorAll.
   */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

  /**
   * Safely parse JSON, returning null on failure.
   */
  const safeParse = (str) => {
    try { return JSON.parse(str); } catch { return null; }
  };

  /**
   * Return a CSRF token if one exists in a meta tag (Flask-WTF pattern).
   */
  const csrfToken = () => {
    const meta = $('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  };

  /* ------------------------------------------------------------------ */
  /*  1. SIDEBAR TOGGLE (mobile)                                         */
  /* ------------------------------------------------------------------ */

  const Sidebar = {
    init() {
      this.sidebar  = $('.sidebar');
      this.toggle   = $('.sidebar-toggle');
      this.overlay  = $('.sidebar-overlay');
      if (!this.sidebar) return;

      this.toggle?.addEventListener('click', () => this.open());
      this.overlay?.addEventListener('click', () => this.close());

      // Close on Escape key
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.close();
      });
    },

    open() {
      this.sidebar?.classList.add('open');
      this.overlay?.classList.add('active');
      document.body.style.overflow = 'hidden';
    },

    close() {
      this.sidebar?.classList.remove('open');
      this.overlay?.classList.remove('active');
      document.body.style.overflow = '';
    },
  };

  /* ------------------------------------------------------------------ */
  /*  2. TAB SWITCHING                                                   */
  /* ------------------------------------------------------------------ */

  const Tabs = {
    init() {
      $$('.tab-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
          const group = btn.closest('.tab-nav');
          if (!group) return;

          const target = btn.dataset.tab;
          if (!target) return;

          // Deactivate siblings
          $$('.tab-btn', group).forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');

          // Find the nearest common parent that holds .tab-content elements
          const container = group.parentElement;
          $$('.tab-content', container).forEach((tc) => {
            tc.classList.toggle('active', tc.id === target);
          });
        });
      });
    },
  };

  /* ------------------------------------------------------------------ */
  /*  3. FLASH MESSAGE AUTO-DISMISS                                      */
  /* ------------------------------------------------------------------ */

  const Flash = {
    init() {
      $$('.flash-message').forEach((msg) => {
        // Optional manual close button
        const closeBtn = $('.flash-close', msg);
        closeBtn?.addEventListener('click', () => this.dismiss(msg));

        // Auto-dismiss
        setTimeout(() => this.dismiss(msg), FLASH_DISMISS_MS);
      });
    },

    dismiss(el) {
      if (!el || el.dataset.dismissed) return;
      el.dataset.dismissed = 'true';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px)';
      setTimeout(() => el.remove(), 300);
    },
  };

  /* ------------------------------------------------------------------ */
  /*  4. CHART RENDERING (Plotly wrapper)                                */
  /* ------------------------------------------------------------------ */

  const Charts = {
    /**
     * Render a single Plotly chart into the given element.
     * @param {string} elementId  DOM id of the container div.
     * @param {object|string} chartJSON  Plotly figure (data + layout) or JSON string.
     */
    render(elementId, chartJSON) {
      const el = document.getElementById(elementId);
      if (!el) return;

      const fig = typeof chartJSON === 'string' ? safeParse(chartJSON) : chartJSON;
      if (!fig) { console.warn(`FitAI: invalid chart JSON for #${elementId}`); return; }

      const layout = Object.assign({}, PLOTLY_DARK_LAYOUT, fig.layout || {});
      const data   = fig.data || [];

      if (typeof Plotly !== 'undefined') {
        Plotly.newPlot(el, data, layout, PLOTLY_CONFIG);
      } else {
        console.warn('FitAI: Plotly is not loaded — skipping chart render.');
      }
    },

    /**
     * Auto-discover all elements with a [data-chart] attribute and render.
     * The attribute value should be a JSON string or an id referencing a
     * <script type="application/json"> block.
     */
    renderAll() {
      $$('[data-chart]').forEach((el) => {
        const raw = el.dataset.chart;
        // Try inline JSON first
        let json = safeParse(raw);
        if (!json) {
          // Treat value as an id to a JSON script block
          const script = document.getElementById(raw);
          if (script) json = safeParse(script.textContent);
        }
        if (json) this.render(el.id, json);
      });
    },
  };

  /* ------------------------------------------------------------------ */
  /*  5. AJAX FORM SUBMISSION                                            */
  /* ------------------------------------------------------------------ */

  const Forms = {
    /**
     * Submit a form via AJAX POST and call onSuccess / onError.
     * @param {string}   formId    DOM id of the <form>.
     * @param {string}   url       POST endpoint (defaults to form.action).
     * @param {Function} onSuccess Callback receiving the parsed JSON response.
     * @param {Function} [onError] Optional error callback.
     */
    async submit(formId, url, onSuccess, onError) {
      const form = document.getElementById(formId);
      if (!form) return;

      const btn = $('button[type="submit"], .btn-primary', form);
      const origHTML = btn ? btn.innerHTML : '';

      try {
        // Loading state
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner"></span> Saving…';
        }

        const formData = new FormData(form);

        const res = await fetch(url || form.action, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken() },
          body: formData,
        });

        const payload = await res.json().catch(() => null);

        if (res.ok) {
          if (typeof onSuccess === 'function') onSuccess(payload);
          else Toast.show(payload?.message || 'Saved successfully!', 'success');
        } else {
          const msg = payload?.error || `Request failed (${res.status})`;
          if (typeof onError === 'function') onError(msg, payload);
          else Toast.show(msg, 'error');
        }
      } catch (err) {
        console.error('FitAI form submit error:', err);
        const msg = 'Network error — please try again.';
        if (typeof onError === 'function') onError(msg);
        else Toast.show(msg, 'error');
      } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = origHTML; }
      }
    },
  };

  /* ------------------------------------------------------------------ */
  /*  6. AI CHAT                                                         */
  /* ------------------------------------------------------------------ */

  const Chat = {
    init() {
      this.container  = $('.chat-messages');
      this.input      = $('.chat-input');
      this.sendBtn    = $('.chat-send-btn');
      if (!this.container || !this.input) return;

      this.sendBtn?.addEventListener('click', () => this.send());
      this.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.send();
        }
      });
    },

    /**
     * Post the user's message to /ai/chat, show typing indicator, render
     * the AI response bubble.
     */
    async send() {
      const text = this.input.value.trim();
      if (!text) return;

      // Render user bubble
      this.appendMessage(text, 'user');
      this.input.value = '';
      this.scrollToBottom();

      // Typing indicator
      const typing = this.showTyping();

      try {
        const res = await fetch('/ai/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken(),
          },
          body: JSON.stringify({ message: text }),
        });

        const data = await res.json().catch(() => ({}));

        // Ensure indicator was visible for at least TYPING_INDICATOR_DELAY
        await new Promise((r) => setTimeout(r, TYPING_INDICATOR_DELAY));
        typing.remove();

        if (res.ok) {
          this.appendMessage(data.response || data.message || 'No response.', 'ai');
        } else {
          this.appendMessage(data.error || 'Sorry, something went wrong.', 'ai error');
        }
      } catch (err) {
        console.error('FitAI chat error:', err);
        typing.remove();
        this.appendMessage('Network error — please try again.', 'ai error');
      }

      this.scrollToBottom();
    },

    /**
     * Create and append a message bubble.
     */
    appendMessage(text, cls) {
      const div = document.createElement('div');
      div.className = `message ${cls}`;
      div.textContent = text;
      this.container.appendChild(div);
    },

    /**
     * Show the three-dot typing indicator and return the element reference.
     */
    showTyping() {
      const div = document.createElement('div');
      div.className = 'message ai typing-indicator';
      div.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
      this.container.appendChild(div);
      this.scrollToBottom();
      return div;
    },

    scrollToBottom() {
      if (this.container) {
        this.container.scrollTop = this.container.scrollHeight;
      }
    },
  };

  /* ------------------------------------------------------------------ */
  /*  7. TRACKING FORM QUICK-LOG                                         */
  /* ------------------------------------------------------------------ */

  const Tracking = {
    init() {
      $$('.quick-log-form').forEach((form) => {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const url = form.action || form.dataset.url;
          const btn = $('button[type="submit"]', form);
          const origHTML = btn ? btn.innerHTML : '';

          try {
            if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>'; }

            const res = await fetch(url, {
              method: 'POST',
              headers: { 'X-CSRFToken': csrfToken() },
              body: new FormData(form),
            });
            const data = await res.json().catch(() => ({}));

            if (res.ok) {
              Toast.show(data.message || 'Logged!', 'success');
              form.reset();
            } else {
              Toast.show(data.error || 'Could not save entry.', 'error');
            }
          } catch (err) {
            console.error('FitAI tracking error:', err);
            Toast.show('Network error — try again.', 'error');
          } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = origHTML; }
          }
        });
      });
    },
  };

  /* ------------------------------------------------------------------ */
  /*  8. TOAST NOTIFICATIONS                                             */
  /* ------------------------------------------------------------------ */

  const Toast = {
    _container: null,

    /**
     * Ensure the fixed toast wrapper exists.
     */
    _getContainer() {
      if (!this._container) {
        this._container = document.createElement('div');
        this._container.className = 'toast-container';
        document.body.appendChild(this._container);
      }
      return this._container;
    },

    /**
     * Show a toast notification.
     * @param {string} message  Text to display.
     * @param {string} type     'success' | 'error' | 'info' | 'warning'
     */
    show(message, type = 'success') {
      const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠',
      };

      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-text">${this._escapeHTML(message)}</span>
      `;

      this._getContainer().appendChild(toast);

      // Trigger reflow then add visible class for transition
      requestAnimationFrame(() => toast.classList.add('show'));

      setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove(), { once: true });
        // Fallback removal in case transitionend doesn't fire
        setTimeout(() => toast.remove(), 400);
      }, TOAST_DISMISS_MS);
    },

    /**
     * Basic HTML escaping to prevent injection in toast messages.
     */
    _escapeHTML(str) {
      const div = document.createElement('div');
      div.textContent = str;
      return div.innerHTML;
    },
  };

  /* ------------------------------------------------------------------ */
  /*  9. LOADING STATES                                                  */
  /* ------------------------------------------------------------------ */

  const Loading = {
    /**
     * Replace an element's content with a skeleton/spinner.
     */
    show(elementId) {
      const el = document.getElementById(elementId);
      if (!el) return;
      el.dataset.originalContent = el.innerHTML;
      el.innerHTML = `
        <div class="loading-state">
          <div class="skeleton" style="height:20px;width:80%;margin-bottom:12px;border-radius:8px;"></div>
          <div class="skeleton" style="height:20px;width:60%;margin-bottom:12px;border-radius:8px;"></div>
          <div class="skeleton" style="height:20px;width:70%;border-radius:8px;"></div>
        </div>`;
    },

    /**
     * Restore the element's original content.
     */
    hide(elementId) {
      const el = document.getElementById(elementId);
      if (!el) return;
      if (el.dataset.originalContent !== undefined) {
        el.innerHTML = el.dataset.originalContent;
        delete el.dataset.originalContent;
      } else {
        const loader = $('.loading-state', el);
        loader?.remove();
      }
    },
  };

  /* ------------------------------------------------------------------ */
  /*  10. MOTIVATION GENERATOR                                           */
  /* ------------------------------------------------------------------ */

  const Motivation = {
    /**
     * Fetch a motivational quote from the AI endpoint and inject it into the
     * #motivation-card element (or the provided selector).
     */
    async get(selector = '#motivation-text') {
      const el = $(selector);
      if (!el) return;

      el.style.opacity = '0.5';

      try {
        const res = await fetch('/ai/motivation', {
          headers: { 'X-CSRFToken': csrfToken() },
        });
        const data = await res.json().catch(() => ({}));

        if (res.ok) {
          el.textContent = data.quote || data.message || data.motivation || 'Keep pushing forward!';
        } else {
          el.textContent = 'Stay consistent — results follow effort.';
        }
      } catch {
        el.textContent = 'Every rep counts. Keep going!';
      } finally {
        el.style.opacity = '1';
      }
    },
  };

  /* ------------------------------------------------------------------ */
  /*  11. SMOOTH SCROLL ANIMATIONS                                       */
  /* ------------------------------------------------------------------ */

  const ScrollAnimations = {
    init() {
      if (!('IntersectionObserver' in window)) return;

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('fade-in');
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
      );

      $$('.animate-on-scroll').forEach((el) => observer.observe(el));
    },
  };

  /* ------------------------------------------------------------------ */
  /*  12. KPI COUNTER ANIMATION                                          */
  /* ------------------------------------------------------------------ */

  const CounterAnimation = {
    init() {
      if (!('IntersectionObserver' in window)) {
        // Fallback: just show the numbers
        return;
      }

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              this.animate(entry.target);
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.3 }
      );

      $$('.kpi-value[data-count]').forEach((el) => observer.observe(el));
    },

    /**
     * Animate a number from 0 to its data-count value.
     */
    animate(el) {
      const target  = parseFloat(el.dataset.count);
      const decimals = (el.dataset.decimals !== undefined) ? parseInt(el.dataset.decimals, 10) : 0;
      const suffix   = el.dataset.suffix || '';
      const prefix   = el.dataset.prefix || '';
      const start    = performance.now();

      const step = (now) => {
        const elapsed  = now - start;
        const progress = Math.min(elapsed / COUNTER_DURATION_MS, 1);
        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;

        el.textContent = `${prefix}${current.toFixed(decimals)}${suffix}`;

        if (progress < 1) requestAnimationFrame(step);
      };

      requestAnimationFrame(step);
    },
  };

  /* ------------------------------------------------------------------ */
  /*  13. CONFIRM DIALOGS                                                */
  /* ------------------------------------------------------------------ */

  const Confirm = {
    init() {
      $$('[data-confirm]').forEach((el) => {
        el.addEventListener('click', (e) => {
          const msg = el.dataset.confirm || 'Are you sure?';
          if (!window.confirm(msg)) {
            e.preventDefault();
            e.stopImmediatePropagation();
          }
        });
      });
    },
  };

  /* ------------------------------------------------------------------ */
  /*  14. DARK / LIGHT TOGGLE (optional, defaults to dark)               */
  /* ------------------------------------------------------------------ */

  const Theme = {
    init() {
      const toggle = $('.theme-toggle');
      if (!toggle) return;

      const saved = localStorage.getItem('fitai-theme') || 'dark';
      document.documentElement.setAttribute('data-theme', saved);

      toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('fitai-theme', next);
      });
    },
  };

  /* ------------------------------------------------------------------ */
  /*  PUBLIC API — attach to window so templates can call directly       */
  /* ------------------------------------------------------------------ */

  window.FitAI = {
    renderChart:   (id, json) => Charts.render(id, json),
    renderAllCharts: ()       => Charts.renderAll(),
    submitForm:    (formId, url, onSuccess, onError) => Forms.submit(formId, url, onSuccess, onError),
    sendChat:      ()         => Chat.send(),
    showToast:     (msg, type) => Toast.show(msg, type),
    showLoading:   (id)       => Loading.show(id),
    hideLoading:   (id)       => Loading.hide(id),
    getMotivation: (sel)      => Motivation.get(sel),
  };

  /* ------------------------------------------------------------------ */
  /*  INIT ON DOM READY                                                  */
  /* ------------------------------------------------------------------ */

  document.addEventListener('DOMContentLoaded', () => {
    Sidebar.init();
    Tabs.init();
    Flash.init();
    Charts.renderAll();
    Chat.init();
    Tracking.init();
    ScrollAnimations.init();
    CounterAnimation.init();
    Confirm.init();
    Theme.init();
  });
})();
