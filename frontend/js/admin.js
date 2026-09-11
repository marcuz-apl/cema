/* CEMA Operations Deck — client controller (vanilla JS, no deps). */
(function () {
  'use strict';

  const KEY_STORE = 'cema_admin_key';
  const THEME_STORE = 'cema_admin_theme';
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const state = {
    key: sessionStorage.getItem(KEY_STORE) || '',
    status: null,
    events: { items: [], total: 0, offset: 0, limit: 50 },
    poll: null,
    bfPoll: null,
    sortBy: 'event_time_utc',
    sortDir: 'desc',
  };

  let confirmCb = null;

  /* ── fetch helpers ─────────────────────────── */
  async function adminFetch(url, opts = {}) {
    opts.headers = Object.assign({
      'X-Admin-Key': state.key,
      ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
    }, opts.headers || {});
    const res = await fetch(url, opts);
    if (res.status === 401) {
      forceGate();
      throw new Error('Session expired — re-enter passkey.');
    }
    let data = null;
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('json')) data = await res.json();
    else data = await res.blob();
    if (!res.ok) {
      const detail = data && data.detail ? (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(', ') : data.detail) : res.statusText;
      throw new Error(detail);
    }
    return data;
  }

  /* ── toasts ────────────────────────────────── */
  function toast(msg, kind = 'info') {
    const el = document.createElement('div');
    el.className = `toast ${kind}`;
    el.textContent = msg;
    $('#toasts').appendChild(el);
    setTimeout(() => el.remove(), 4200);
  }

  /* ── auth gate ─────────────────────────────── */
  function forceGate() {
    sessionStorage.removeItem(KEY_STORE);
    state.key = '';
    $('#authGate').classList.remove('hidden');
    $('#app').classList.add('hidden');
  }

  async function unlock() {
    const input = $('#authKey');
    const key = input.value.trim();
    if (!key) return;
    $('#authBtn').disabled = true;
    $('#authError').classList.add('hidden');
    try {
      const probe = await fetch('/api/admin/auth', {
        method: 'POST',
        headers: { 'X-Admin-Key': key },
      });
      if (!probe.ok) throw new Error('Invalid passkey.');
      state.key = key;
      sessionStorage.setItem(KEY_STORE, key);
      input.value = '';
      $('#authGate').classList.add('hidden');
      $('#app').classList.remove('hidden');
      boot();
      toast('Deck unlocked — operator session live', 'ok');
    } catch (err) {
      $('#authError').textContent = err.message;
      $('#authError').classList.remove('hidden');
    } finally {
      $('#authBtn').disabled = false;
    }
  }

  async function tryResume() {
    if (!state.key) return;
    try {
      await adminFetch('/api/admin/auth', { method: 'POST' });
      $('#authGate').classList.add('hidden');
      $('#app').classList.remove('hidden');
      boot();
    } catch (e) { /* forced gate via 401 */ }
  }

  /* ── clock / theme ─────────────────────────── */
  function tickClock() {
    const now = new Date();
    $('#clock').textContent = now.toISOString().slice(11, 19) + ' UTC';
  }

  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    $('#themeBtn').textContent = t === 'dark' ? '☀' : '☾';
  }

  /* ── status render ─────────────────────────── */
  function renderProviders() {
    const st = state.status;
    const wrap = $('#providers');
    if (!st || !st.providers) return;
    const canonicalKeys = ['nrcan', 'cenc', 'usgs'];
    const providersList = canonicalKeys
      .filter((k) => st.providers[k])
      .map((k) => st.providers[k]);
    const list = providersList.length ? providersList : Object.values(st.providers);

    wrap.innerHTML = list.map((p) => `
      <div class="provider-card">
        <div class="pc-head">
          <div>
            <div class="pc-name">${esc(p.name)}</div>
            <div class="pc-tag">${esc(p.role || p.source)}</div>
          </div>
          <span class="pc-status ${p.reachable ? 'ok' : 'down'}">${p.reachable ? '◉ ONLINE' : '◉ DOWN'}</span>
        </div>
        <div class="pc-metrics">
          <div class="pc-metric"><span class="mono">${p.catalog_count != null ? p.catalog_count.toLocaleString() : '—'}</span><small>CATALOG</small></div>
          <div class="pc-metric"><span class="mono">${p.latency_ms != null ? p.latency_ms + 'ms' : '—'}</span><small>PING</small></div>
          <div class="pc-metric"><span class="mono">${esc((p.status || '').toUpperCase())}</span><small>HEALTH</small></div>
        </div>
        <div class="pc-aoi">${esc(p.source)} · ${Array.isArray(p.aoi) ? 'AOI ' + p.aoi.join(', ') : esc(p.aoi || '')}</div>
      </div>`).join('');
  }

  function renderKPIs() {
    const db = state.status.database;
    const caCnt = db.per_region && db.per_region.canada != null ? db.per_region.canada.toLocaleString() : '—';
    const cnCnt = db.per_region && db.per_region.china != null ? db.per_region.china.toLocaleString() : '—';
    const kpis = [
      { v: db.total_records.toLocaleString(), c: '', l: 'TOTAL EVENTS', s: `CA: ${caCnt} · CN: ${cnCnt}` },
      { v: db.earliest_date ? db.earliest_date.slice(0, 10) : '—', c: '', l: 'EARLIEST UTC' },
      { v: db.latest_date ? db.latest_date.slice(0, 10) : '—', c: '', l: 'LATEST UTC' },
      { v: (db.db_size_mb + db.wal_size_mb).toFixed(2) + ' MB', c: 'gold', l: 'STORAGE + WAL', s: `ca ${(db.db_sizes.canada / 1024 / 1024).toFixed(1)}M · ch ${(db.db_sizes.china / 1024 / 1024).toFixed(1)}M` },
    ];
    $('#kpiRow').innerHTML = kpis.map((k) => `
      <div class="kpi">
        <span class="mono ${k.c || 'red'}">${esc(k.v)}</span>
        <small>${k.l}</small>
        ${k.s ? `<div class="kpi-sub mono">${esc(k.s)}</div>` : ''}
      </div>`).join('');
  }

  function renderDensity() {
    const db = state.status.database;
    const years = db.by_year_list.slice(0, 10);
    const maxY = Math.max(...years.map((y) => y.count), 1);
    $('#yearDensity').innerHTML = years.map((y) => `
      <div class="density-row">
        <span class="lbl">${y.year}</span>
        <div class="track"><div class="fill" style="width:${Math.round(y.count / maxY * 100)}%"></div></div>
        <span class="cnt">${y.count.toLocaleString()}</span>
      </div>`).join('') || '<div class="empty">no data</div>';

    const mags = db.magnitude_distribution;
    const maxM = Math.max(...Object.values(mags), 1);
    $('#magDist').innerHTML = Object.entries(mags).map(([label, count]) => `
      <div class="density-row">
        <span class="lbl">${label}</span>
        <div class="track"><div class="fill" style="width:${Math.round(count / maxM * 100)}%"></div></div>
        <span class="cnt">${count.toLocaleString()}</span>
      </div>`).join('');
  }

  async function refreshStatus(quiet = true) {
    try {
      const st = await adminFetch('/api/admin/status');
      state.status = st;
      renderProviders();
      renderKPIs();
      renderDensity();
      $('#eventsTotal').textContent = `${st.database.total_records.toLocaleString()} records · dual catalog`;
      renderBackfillStub(st.backfill_state, st.sync_state);
      if (st.backfill_state && st.backfill_state.is_running && !state.bfPoll) {
        startBackfillPoll();
      }
      if (!quiet) toast('Telemetry refreshed', 'ok');
    } catch (e) { if (!quiet) toast(e.message, 'err'); }
  }

  /* ── backfill engine ───────────────────────── */
  function setPreset(range) {
    $$('.chip-btn').forEach((b) => b.classList.toggle('active', b.dataset.range === range));
    const today = new Date();
    const iso = (d) => d.toISOString().slice(0, 10);
    if (range === 'full') {
      $('#bfStart').value = '2020-01-01';
      $('#bfEnd').value = iso(today);
    } else {
      $('#bfStart').value = `${range}-01-01`;
      $('#bfEnd').value = iso(new Date(`${range}-12-31`));
    }
  }

  function renderBackfillStub(bf, sync) {
    const mode = bf.mode === 'merge' ? 'MERGE' : 'BACKFILL';
    if (bf.is_running) {
      const pct = bf.windows_total ? Math.min(100, Math.round(bf.windows_done / bf.windows_total * 100)) : 0;
      $('#bfStatus').className = 'bf-status mono running';
      $('#bfStatus').textContent = `RUNNING ${mode} · ${bf.current_window || '…'} — started ${(bf.started_at || '').slice(11, 19)}Z`;
      $('#bfBar').style.width = pct + '%';
      $('#bfPercent').textContent = pct + '%';
      $('#bfWindow').textContent = `${bf.windows_done}/${bf.windows_total}`;
      $('#bfFetched').textContent = bf.fetched.toLocaleString();
      $('#bfInserted').textContent = bf.inserted.toLocaleString();
      $('#bfRange').textContent = `${bf.start_date} … ${bf.end_date} · M≥${bf.min_mag}`;
    } else if (bf.status === 'complete') {
      $('#bfStatus').className = 'bf-status mono done';
      $('#bfStatus').textContent = `COMPLETE ${mode} · ${JSON.stringify(bf.per_region)}`;
      $('#bfPercent').textContent = '100%';
      $('#bfBar').style.width = '100%';
      $('#bfFetched').textContent = bf.fetched.toLocaleString();
      $('#bfInserted').textContent = bf.inserted.toLocaleString();
    } else if (bf.status === 'failed') {
      $('#bfStatus').className = 'bf-status mono err';
      $('#bfStatus').textContent = `FAILED · ${bf.error || 'see log'}`;
    } else {
      $('#bfStatus').className = 'bf-status mono';
      $('#bfStatus').textContent = 'IDLE — awaiting command';
      $('#bfPercent').textContent = '0%';
      $('#bfBar').style.width = '0%';
      $('#bfInserted').textContent = '—';
    }
    if (bf.current_window) $('#bfRange').textContent = `${bf.start_date} … ${bf.end_date} · M≥${bf.min_mag}`;

    const resetBtn = $('#bfResetBtn');
    if (resetBtn) {
      if (bf.status === 'complete' || bf.status === 'failed') {
        resetBtn.classList.remove('hidden');
      } else {
        resetBtn.classList.add('hidden');
      }
    }
  }

  function renderLog(lines) {
    const body = $('#bfLog');
    if (!lines || !lines.length) return;
    body.innerHTML = lines.slice(-60).map((l) => esc(l)).join('\n');
    body.scrollTop = body.scrollHeight;
  }

  function startBackfillPoll() {
    clearInterval(state.bfPoll);
    let wasRunning = false;
    state.bfPoll = setInterval(async () => {
      try {
        const bf = await adminFetch('/api/admin/backfill/status');
        if (bf.is_running) wasRunning = true;
        renderBackfillStub(bf, null);
        renderLog(bf.log);
        if (!bf.is_running) {
          clearInterval(state.bfPoll);
          state.bfPoll = null;
          if (wasRunning && bf.status === 'complete') toast('Backfill job complete', 'ok');
          refreshStatus(true);
        }
      } catch (e) { clearInterval(state.bfPoll); state.bfPoll = null; }
    }, 1500);
  }

  async function launchBackfill() {
    const payload = {
      start_date: $('#bfStart').value,
      end_date: $('#bfEnd').value,
      min_mag: parseFloat($('#bfMag').value),
      chunk_days: parseInt($('#bfChunk').value, 10),
      mode: $('#bfMode').value,
      regions: $('#bfRegions').value,
      source: $('#bfSource') ? $('#bfSource').value : 'usgs',
    };
    if (!payload.start_date || !payload.end_date) {
      toast('Set a date range first.', 'err');
      return;
    }
    try {
      await adminFetch('/api/admin/backfill', { method: 'POST', body: JSON.stringify(payload) });
      toast('Backfill queued — monitoring job…', 'info');
      renderLog(['$ cema-ops backfill --queued']);
      startBackfillPoll();
    } catch (e) { toast(e.message, 'err'); }
  }

  /* ── sync (live refresh) ───────────────────── */
  async function syncAll() {
    try {
      await adminFetch('/api/admin/sync/all', { method: 'POST' });
      toast('Live re-sync queued for both AOIs (rolling 7d)', 'info');
      startBackfillPoll();
    } catch (e) { toast(e.message, 'err'); }
  }

  /* ── maintenance tools ─────────────────────── */
  function confirmDialog(title, msg, cb) {
    $('#confirmTitle').textContent = title;
    $('#confirmMsg').textContent = msg;
    $('#confirmModal').classList.remove('hidden');
    confirmCb = cb;
  }

  async function runTool(fn, label) {
    try {
      const res = await fn();
      toast(`${label} → ${JSON.stringify(res)}`, 'ok');
      refreshStatus(true);
    } catch (e) { toast(e.message, 'err'); }
  }

  async function exportCatalog() {
    toast('Bundling both catalogs…', 'info');
    try {
      const blob = await adminFetch('/api/admin/db/download');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cema-catalog-${new Date().toISOString().slice(0, 10)}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast('Catalog export downloaded', 'ok');
    } catch (e) { toast(e.message, 'err'); }
  }

  /* ── event moderation ──────────────────────── */
  function magClass(m) {
    if (m >= 6) return 'mag-x';
    if (m >= 4.5) return 'mag-l';
    return 'mag-m';
  }

  function eventsFilters() {
    return {
      region: $('#mfRegion').value,
      source: $('#mfSource').value,
      min_mag: $('#mfMinMag').value,
      search: $('#mfSearch').value.trim(),
      sort_by: state.sortBy,
      sort_dir: state.sortDir,
    };
  }

  async function loadEvents(resetOffset = false) {
    if (resetOffset) state.events.offset = 0;
    const f = eventsFilters();
    const params = new URLSearchParams({
      limit: state.events.limit,
      offset: state.events.offset,
      sort_by: f.sort_by,
      sort_dir: f.sort_dir,
    });
    if (f.region) params.set('region', f.region);
    if (f.source) params.set('source', f.source);
    if (f.min_mag) params.set('min_mag', f.min_mag);
    if (f.search) params.set('search', f.search);
    try {
      const data = await adminFetch('/api/admin/earthquakes?' + params.toString());
      state.events.items = data.items;
      state.events.total = data.total;
      renderEvents();
    } catch (e) { toast(e.message, 'err'); }
  }

  function renderEvents() {
    const body = $('#eventsBody');
    if (!state.events.items.length) {
      body.innerHTML = '<tr><td colspan="8" class="empty">No events match the current filters.</td></tr>';
    } else {
      body.innerHTML = state.events.items.map((ev) => `
        <tr>
          <td><span class="mono">${esc(ev.event_time_utc.replace('T', ' ').slice(0, 19))}</span></td>
          <td><span class="mag-pill ${magClass(ev.magnitude)}">${ev.magnitude.toFixed(1)}</span></td>
          <td><span class="region-chip ${ev.region}">${esc(ev.region.toUpperCase())}</span></td>
          <td class="mono">${Number(ev.latitude).toFixed(2)}</td>
          <td class="mono">${Number(ev.longitude).toFixed(2)}</td>
          <td class="mono">${Number(ev.depth_km).toFixed(1)} km</td>
          <td class="mono">${esc(ev.source)}</td>
          <td><button class="row-del" data-id="${ev.id}" data-region="${ev.region}">✕</button></td>
        </tr>`).join('');
    }
    const { offset, limit } = state.events;
    const lo = state.events.total ? offset + 1 : 0;
    const hi = Math.min(offset + limit, state.events.total);
    $('#pgInfo').textContent = `${lo} – ${hi} of ${state.events.total.toLocaleString()}`;
    if ($('#pgFirst')) $('#pgFirst').disabled = offset <= 0;
    $('#pgPrev').disabled = offset <= 0;
    $('#pgNext').disabled = offset + limit >= state.events.total;
    if ($('#pgLast')) $('#pgLast').disabled = offset + limit >= state.events.total;
  }

  /* ── register event ────────────────────────── */
  function openRegister() {
    $('#regTime').value = new Date().toISOString().slice(0, 16);
    $('#registerModal').classList.remove('hidden');
  }

  async function saveRegister() {
    const payload = {
      region: $('#regRegion').value,
      event_time_utc: new Date($('#regTime').value).toISOString(),
      latitude: parseFloat($('#regLat').value),
      longitude: parseFloat($('#regLon').value),
      depth_km: parseFloat($('#regDepth').value),
      magnitude: parseFloat($('#regMag').value),
      source: $('#regSource').value.trim() || 'OPERATOR',
    };
    if (isNaN(payload.latitude) || isNaN(payload.longitude) || isNaN(payload.magnitude)) {
      toast('Latitude, longitude and magnitude are required.', 'err');
      return;
    }
    try {
      await adminFetch('/api/admin/earthquakes', { method: 'POST', body: JSON.stringify(payload) });
      $('#registerModal').classList.add('hidden');
      toast('Event registered to verified catalog', 'ok');
      refreshStatus(true);
      loadEvents(true);
    } catch (e) { toast(e.message, 'err'); }
  }

  /* ── boot / wiring ─────────────────────────── */
  function boot() {
    tickClock();
    setInterval(tickClock, 1000);
    refreshStatus(false);
    loadEvents(true);
    if (syncInterval) clearInterval(syncInterval);
    syncInterval = setInterval(() => { if (state.key) adminFetch('/api/admin/status').then(() => {}).catch(() => {}); }, 30000);
  }
  let syncInterval = null;

  /* event wiring */
  $('#authBtn').addEventListener('click', unlock);
  $('#authKey').addEventListener('keydown', (e) => { if (e.key === 'Enter') unlock(); });
  $('#publicMapBtn').addEventListener('click', (e) => {
    e.preventDefault();
    sessionStorage.removeItem(KEY_STORE);
    state.key = '';
    window.location.href = '/';
  });
  function openPasskeyModal() {
    $('#curPasskey').value = '';
    $('#newPasskey').value = '';
    $('#confirmPasskey').value = '';
    $('#passkeyError').textContent = '';
    $('#passkeyError').classList.add('hidden');
    $('#passkeyModal').classList.remove('hidden');
    setTimeout(() => $('#curPasskey').focus(), 50);
  }

  function closePasskeyModal() {
    $('#passkeyModal').classList.add('hidden');
  }

  function submitPasskeyChange() {
    const cur = $('#curPasskey').value.trim();
    const next = $('#newPasskey').value.trim();
    const conf = $('#confirmPasskey').value.trim();
    const errEl = $('#passkeyError');

    errEl.classList.add('hidden');
    errEl.textContent = '';

    if (!cur) {
      errEl.textContent = 'Please enter your current passkey.';
      errEl.classList.remove('hidden');
      $('#curPasskey').focus();
      return;
    }
    if (!next || next.length < 6) {
      errEl.textContent = 'New passkey must be at least 6 characters.';
      errEl.classList.remove('hidden');
      $('#newPasskey').focus();
      return;
    }
    if (next !== conf) {
      errEl.textContent = 'New passkeys do not match.';
      errEl.classList.remove('hidden');
      $('#confirmPasskey').focus();
      return;
    }

    const saveBtn = $('#passkeySave');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Updating...';

    adminFetch('/api/admin/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: cur, new_password: next }),
    })
      .then((r) => {
        toast(r.message || 'Passkey updated successfully', 'ok');
        closePasskeyModal();
        state.key = next;
        sessionStorage.setItem(KEY_STORE, next);
      })
      .catch((e) => {
        errEl.textContent = e.message || 'Failed to update passkey';
        errEl.classList.remove('hidden');
      })
      .finally(() => {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Update Passkey';
      });
  }

  $('#pwdBtn').addEventListener('click', openPasskeyModal);
  $('#passkeyCancel').addEventListener('click', closePasskeyModal);
  $('#passkeySave').addEventListener('click', submitPasskeyChange);
  $('#passkeyModal').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closePasskeyModal();
    if (e.key === 'Enter') submitPasskeyChange();
  });
  $('#themeBtn').addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem(THEME_STORE, next);
  });
  $('#syncAllBtn').addEventListener('click', syncAll);

  $$('.chip-btn').forEach((b) => b.addEventListener('click', () => setPreset(b.dataset.range)));
  $('#bfLaunch').addEventListener('click', launchBackfill);
  if ($('#bfResetBtn')) {
    $('#bfResetBtn').addEventListener('click', async () => {
      try {
        await adminFetch('/api/admin/backfill/reset', { method: 'POST' });
        toast('Backfill engine reset to IDLE', 'ok');
        refreshStatus(true);
      } catch (e) { toast(e.message, 'err'); }
    });
  }

  $('#toolDedup').addEventListener('click', () => {
    confirmDialog('Run deduplication?', 'Removes duplicate events within ≤25 km and ±60 s across both catalogs. This operation is destructive.', () => runTool(() => adminFetch('/api/admin/db/deduplicate', { method: 'POST' }), 'Dedupe'));
  });
  $('#toolPurge').addEventListener('click', () => {
    const floor = $('#purgeFloor').value;
    confirmDialog(`Purge noise (M<${floor})?`, `Permanently deletes all events below magnitude ${floor} from both catalogs.`, () => runTool(() => adminFetch(`/api/admin/db/purge-noise?min_mag=${floor}`, { method: 'POST' }), 'Purge'));
  });
  $('#toolCheckpoint').addEventListener('click', () => runTool(() => adminFetch('/api/admin/db/checkpoint-wal', { method: 'POST' }), 'WAL checkpoint'));
  $('#toolVacuum').addEventListener('click', () => {
    confirmDialog('Vacuum both catalogs?', 'Rebuilds storage and analyzes indexes. Reclaims deleted-space.', () => runTool(() => adminFetch('/api/admin/db/vacuum', { method: 'POST' }), 'Vacuum'));
  });
  $('#toolExport').addEventListener('click', exportCatalog);

  $('#mfApply').addEventListener('click', () => loadEvents(true));
  $('#mfReset').addEventListener('click', () => {
    ['#mfRegion', '#mfSource', '#mfMinMag'].forEach((s) => { $(s).value = ''; });
    $('#mfSearch').value = '';
    loadEvents(true);
  });
  $('#mfSearch').addEventListener('keydown', (e) => { if (e.key === 'Enter') loadEvents(true); });
  if ($('#pgFirst')) {
    $('#pgFirst').addEventListener('click', () => { state.events.offset = 0; loadEvents(); });
  }
  $('#pgPrev').addEventListener('click', () => { state.events.offset = Math.max(0, state.events.offset - state.events.limit); loadEvents(); });
  $('#pgNext').addEventListener('click', () => { state.events.offset += state.events.limit; loadEvents(); });
  if ($('#pgLast')) {
    $('#pgLast').addEventListener('click', () => {
      const lastOffset = Math.floor(Math.max(0, state.events.total - 1) / state.events.limit) * state.events.limit;
      state.events.offset = lastOffset;
      loadEvents();
    });
  }

  if ($('#purgeFloor')) {
    $('#purgeFloor').addEventListener('click', (e) => e.stopPropagation());
    $('#purgeFloor').addEventListener('change', (e) => e.stopPropagation());
  }

  $('#eventsBody').addEventListener('click', (e) => {
    const btn = e.target.closest('.row-del');
    if (!btn) return;
    const id = btn.dataset.id;
    const region = btn.dataset.region;
    confirmDialog('Delete event?', `This permanently removes event #${id} from the ${region.toUpperCase()} catalog.`, async () => {
      try {
        await adminFetch('/api/admin/earthquakes', { method: 'DELETE', body: JSON.stringify({ id: parseInt(id, 10), region }) });
        toast('Event deleted', 'ok');
        refreshStatus(true);
        loadEvents();
      } catch (err) { toast(err.message, 'err'); }
    });
  });

  $$('th.sortable').forEach((th) => th.addEventListener('click', () => {
    const by = th.dataset.sort;
    if (state.sortBy === by) state.sortDir = state.sortDir === 'desc' ? 'asc' : 'desc';
    else { state.sortBy = by; state.sortDir = 'desc'; }
    loadEvents(true);
  }));

  $('#registerBtn').addEventListener('click', openRegister);
  $('#regCancel').addEventListener('click', () => $('#registerModal').classList.add('hidden'));
  $('#regSave').addEventListener('click', saveRegister);

  $('#confirmCancel').addEventListener('click', () => $('#confirmModal').classList.add('hidden'));
  $('#confirmOk').addEventListener('click', () => {
    $('#confirmModal').classList.add('hidden');
    if (confirmCb) { const cb = confirmCb; confirmCb = null; cb(); }
  });
  [['confirmModal', null], ['registerModal', null], ['passkeyModal', null]].forEach(([modalId]) => {
    $('#' + modalId).addEventListener('click', (e) => { if (e.target.id === modalId) e.target.classList.add('hidden'); });
  });

  /* init */
  applyTheme(localStorage.getItem(THEME_STORE) || 'dark');
  setPreset('2023');
  tryResume();
})();