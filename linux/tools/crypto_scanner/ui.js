/**
 * 🪙 Flowork Dynamic Tool UI Renderer — Crypto Scanner
 * Zero-Corner Dynamic Pod Controller
 */

export default {
  /**
   * Mounts the live HUD animation into .fl-live-active-slot
   */
  mountLive(slotEl, details = {}, stepIdx = '') {
    if (!slotEl) return null;
    const d = (details && details.details && typeof details.details === 'object') ? { ...details, ...details.details } : (details || {});
    const pair = String(d.pair || d.symbol || 'BTC/USDT').toUpperCase();
    const tf = String(d.timeframe || '1h');

    const pod = document.createElement('div');
    pod.className = 'fl-crypto-scanner-pod';
    pod.setAttribute('data-live-step', String(stepIdx));
    pod._spawnTime = Date.now();

    pod.innerHTML = `
      <div class="fl-crypto-header">
        <div class="fl-crypto-title-wrap">
          <div class="fl-crypto-radar-orb">
            <div class="fl-crypto-orb-core"></div>
          </div>
          <span class="fl-crypto-label">CRYPTO SCANNER</span>
          <span class="fl-crypto-pair-badge">${escapeHtml(pair)} • ${escapeHtml(tf)}</span>
        </div>
        <div class="fl-crypto-status-pill">
          <span class="fl-crypto-pulse-dot"></span>
          <span class="fl-crypto-status-text">SCANNING ORDERBOOK</span>
        </div>
      </div>

      <div class="fl-crypto-telemetry-strip">
        <div class="fl-crypto-metric-pill">
          <span class="fl-crypto-metric-name">LAST:</span>
          <span class="fl-crypto-metric-val fl-crypto-val-price">STREAMING...</span>
        </div>
        <div class="fl-crypto-metric-pill">
          <span class="fl-crypto-metric-name">24H:</span>
          <span class="fl-crypto-metric-val fl-crypto-val-change">--</span>
        </div>
        <div class="fl-crypto-metric-pill">
          <span class="fl-crypto-metric-name">LIQUIDITY:</span>
          <span class="fl-crypto-metric-val fl-crypto-val-depth">DEEP</span>
        </div>
      </div>

      <div class="fl-crypto-meter-track">
        <div class="fl-crypto-meter-fill" style="width: 35%;"></div>
      </div>

      <div class="fl-crypto-footer">
        <span class="fl-crypto-footer-sop">📖 SOP: tools/crypto_scanner/SKILL.md</span>
        <span class="fl-crypto-footer-timer">0.05s • REALTIME MESH</span>
      </div>
    `;

    slotEl.appendChild(pod);

    let progress = 35;
    pod._tickTimer = setInterval(() => {
      if (!pod.isConnected) return;
      progress = (progress + 12) % 100;
      const fill = pod.querySelector('.fl-crypto-meter-fill');
      if (fill) fill.style.width = `${Math.max(15, progress)}%`;
      const elapsed = ((Date.now() - pod._spawnTime) / 1000).toFixed(2);
      const timerEl = pod.querySelector('.fl-crypto-footer-timer');
      if (timerEl) timerEl.textContent = `${elapsed}s • REALTIME MESH`;
    }, 120);

    return pod;
  },

  /**
   * Updates HUD on live terminal stream output
   */
  onStream(slotEl, chunkData) {
    if (!slotEl) return;
    const pod = slotEl.querySelector('.fl-crypto-scanner-pod');
    if (!pod) return;
    // Inspect chunk for price data
    const str = typeof chunkData === 'string' ? chunkData : JSON.stringify(chunkData);
    const pMatch = str.match(/"last_price"\s*:\s*([0-9.]+)/);
    if (pMatch) {
      const priceEl = pod.querySelector('.fl-crypto-val-price');
      if (priceEl) priceEl.textContent = `$${pMatch[1]}`;
    }
  },

  /**
   * Finalizes state when tool execution completes (Exit Code 0)
   */
  onDone(slotEl, outputData) {
    if (!slotEl) return;
    const pod = slotEl.querySelector('.fl-crypto-scanner-pod');
    if (!pod) return;
    if (pod._tickTimer) {
      clearInterval(pod._tickTimer);
      pod._tickTimer = null;
    }

    const statusText = pod.querySelector('.fl-crypto-status-text');
    if (statusText) statusText.textContent = '✓ SCAN COMPLETE (EXIT 0)';

    const fill = pod.querySelector('.fl-crypto-meter-fill');
    if (fill) fill.style.width = '100%';

    // Inject final parsed data if present
    try {
      const data = typeof outputData === 'string' ? JSON.parse(outputData) : outputData;
      if (data && data.metrics) {
        const priceEl = pod.querySelector('.fl-crypto-val-price');
        if (priceEl) priceEl.textContent = `$${data.metrics.last_price}`;
        const chgEl = pod.querySelector('.fl-crypto-val-change');
        if (chgEl) {
          const chg = data.metrics.change_24h_pct;
          chgEl.textContent = `${chg >= 0 ? '+' : ''}${chg}%`;
          chgEl.className = `fl-crypto-metric-val ${chg >= 0 ? 'is-positive' : 'is-negative'}`;
        }
      }
    } catch (_) {}
  }
};

function escapeHtml(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
