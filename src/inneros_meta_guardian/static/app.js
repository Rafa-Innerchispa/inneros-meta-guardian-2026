'use strict';

const steps = [
  ['OBSERVE', 'Ingest real or synthetic infrastructure signals'],
  ['REMEMBER', 'Recall verified AG-60 / Personal Brain memory'],
  ['REASON', 'Meta Muse Spark 1.3 governed analysis'],
  ['APPROVE', 'Explicit human authority gate (Rafael López)'],
  ['ACT', 'Governed virtual execution (fail-safe isolated)'],
  ['VERIFY', 'Independent state readback & VoiceOps proof'],
  ['PROVE', 'Tamper-evident SHA-256 hash-chained audit package'],
];

let current = null;
let currentGrant = null;
let busy = false;

const $ = (id) => document.getElementById(id);
const setText = (id, text) => { if ($(id)) $(id).textContent = String(text); };
const states = { observed: 0, analyzed: 2, approved: 3, executed: 4, verified: 6, failed_safe: 5 };

async function call(path, body) {
  const options = body === undefined ? {} : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function say(msg, good = false) {
  if (!$('toast')) return;
  setText('toast', msg);
  $('toast').className = `toast ${good ? 'good' : ''}`;
}

function disableActions() {
  const s = current?.status || '';
  if ($('analyze')) $('analyze').disabled = busy || s !== 'observed';
  if ($('approve')) $('approve').disabled = busy || s !== 'analyzed' || !current?.policy?.allowed;
  if ($('execute')) $('execute').disabled = busy || s !== 'approved';
  if ($('verify')) $('verify').disabled = busy || s !== 'executed';
  if ($('create')) $('create').disabled = busy;
  if ($('download')) $('download').disabled = !current || busy;

  // Live and Meta buttons
  const hasCurrent = !!current;
  if ($('btn-mint-grant')) $('btn-mint-grant').disabled = busy || !hasCurrent;
  if ($('btn-meta-analyze')) $('btn-meta-analyze').disabled = busy || !currentGrant || s !== 'observed';
  if ($('btn-recall-memory')) $('btn-recall-memory').disabled = busy || !hasCurrent;
}

function stageList() {
  const holder = $('stage-list');
  if (!holder) return;
  holder.replaceChildren();
  if (!current) {
    const d = document.createElement('div');
    d.className = 'empty-workflow';
    d.textContent = 'Ingest live telemetry or create an incident to begin the governed operational loop.';
    holder.append(d);
    return;
  }
  const index = states[current.status] ?? 0;
  for (let i = 0; i < steps.length; i++) {
    const [title, subtitle] = steps[i];
    const done = i <= index;
    const active = !done && i === index + 1;
    const row = document.createElement('div');
    row.className = `stage ${done ? 'done' : (active ? 'active' : '')}`;
    const circle = document.createElement('div');
    circle.className = 'stage-circle';
    circle.textContent = done ? '✓' : String(i + 1);
    const content = document.createElement('div');
    const h = document.createElement('div');
    h.className = 'stage-title';
    h.textContent = title;
    const p = document.createElement('p');
    p.className = 'stage-note';
    p.textContent = done ? (i === 6 ? 'Tamper-evident chain complete' : `${subtitle} · done`) : subtitle;
    content.append(h, p);
    row.append(circle, content);
    holder.append(row);
  }
}

function renderMemory() {
  const box = $('memory-facts');
  if (!box) return;
  box.replaceChildren();
  const facts = current?.memory?.facts || [];
  if (!facts.length) {
    const span = document.createElement('span');
    span.className = 'muted-italic';
    span.textContent = "Click 'Recall Facts' to retrieve verified historical baseline for this site.";
    box.append(span);
    return;
  }
  for (const f of facts) {
    const item = document.createElement('div');
    item.className = 'fact-item';
    const st = document.createElement('strong');
    st.textContent = `[${f.category.toUpperCase()}] ${f.title}`;
    const p = document.createElement('div');
    p.textContent = f.fact;
    item.append(st, p);
    box.append(item);
  }
}

function renderMetaReceipt() {
  const box = $('meta-receipt');
  if (!box) return;
  const receipt = current?.narration?.receipt;
  if (!receipt) {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  box.replaceChildren();
  const header = document.createElement('div');
  header.style.fontWeight = 'bold';
  header.style.color = '#75c8f6';
  header.textContent = `⚡ META RECEIPT: ${receipt.status} (${receipt.model})`;
  const line1 = document.createElement('div');
  line1.textContent = `Token: ${receipt.grant_token ? receipt.grant_token.slice(0, 16) + '...' : 'none'} | Latency: ${receipt.latency_ms}ms | Fallback: ${receipt.local_fallback_applied}`;
  const line2 = document.createElement('div');
  line2.textContent = `Digest: ${receipt.snapshot_digest.slice(0, 16)}... | ReqHash: ${receipt.request_hash.slice(0, 16)}...`;
  box.append(header, line1, line2);
}

function renderCurrent() {
  stageList();
  if ($('incident-details')) $('incident-details').hidden = !current;
  if (current) {
    setText('incident-badge', current.status.toUpperCase());
    setText('incident-id', current.id.slice(0, 8));
    setText('incident-title', current.title);
    setText('incident-digest', current.snapshot_digest || 'None');
    setText('incident-narrative', current.narration?.narrative || 'Reasoning pending.');
    setText('provider-label', current.narration ? `${current.narration.provider} · ${current.narration.truth}` : 'NOT ANALYZED');

    const signals = $('incident-signals');
    if (signals) {
      signals.replaceChildren();
      for (const s of (current.signals || [])) {
        const el = document.createElement('span');
        el.className = 'signal';
        el.textContent = s.name ? `${s.name}: ${s.status || s.value || 'ok'}` : `${s.metric}: ${s.value}`;
        signals.append(el);
      }
    }
    renderMemory();
    renderMetaReceipt();

    if (current.narration?.fallback_reason) {
      say(`Provider fallback: ${current.narration.fallback_reason}`);
    }
  } else {
    setText('incident-badge', 'NO INCIDENT');
    renderMemory();
    if ($('meta-receipt')) $('meta-receipt').hidden = true;
  }
  disableActions();
}

async function refresh() {
  const state = await call('/api/state');
  setText('stat-total', state.incidents.length);
  setText('stat-verified', state.incidents.filter((x) => x.status === 'verified').length);
  setText('stat-integrity', state.audit_integrity.valid ? 'VALID' : 'FAILED');
  if ($('stat-integrity')) {
    $('stat-integrity').className = `stat-number stat-small ${state.audit_integrity.valid ? 'accent-green' : ''}`;
  }

  const logs = $('incident-log');
  if (logs) {
    logs.replaceChildren();
    if (!state.incidents.length) {
      const el = document.createElement('div');
      el.className = 'log-empty';
      el.textContent = 'No evidence recorded yet. Ingest telemetry or create an incident above.';
      logs.append(el);
      return;
    }
    for (const incident of state.incidents) {
      const row = document.createElement('div');
      row.className = 'audit-row';
      const info = document.createElement('div');
      info.className = 'audit-title';
      info.textContent = incident.title;
      const id = document.createElement('small');
      id.textContent = `#${incident.id.slice(0, 8)} · ${incident.site || 'sandbox'} · ${incident.snapshot_digest ? incident.snapshot_digest.slice(0, 12) : ''}...`;
      info.append(id);
      const status = document.createElement('div');
      const label = document.createElement('span');
      label.className = 'state-tag';
      label.textContent = incident.status.toUpperCase();
      status.append(label);
      const source = document.createElement('span');
      source.className = 'truth-tag';
      source.textContent = incident.truth;
      row.append(info, status, source);
      logs.append(row);
    }
  }
}

async function operation(callback) {
  if (busy) return;
  busy = true;
  disableActions();
  say('Processing…');
  try {
    current = await callback();
    say(`Incident ${current.status.toUpperCase()} · saved in local audit log.`, true);
  } catch (e) {
    say(e.message);
  } finally {
    busy = false;
    renderCurrent();
    await refresh().catch((e) => say(e.message));
  }
}

// Event Listeners for Live Ingestion
if ($('btn-live-casa-net')) {
  $('btn-live-casa-net').addEventListener('click', () => {
    currentGrant = null;
    setText('grant-status', 'No active grant. Ingest telemetry to mint grant.');
    operation(() => call('/api/incidents/live', { site: 'casa', category: 'network' }));
  });
}
if ($('btn-live-casa-srv')) {
  $('btn-live-casa-srv').addEventListener('click', () => {
    currentGrant = null;
    setText('grant-status', 'No active grant. Ingest telemetry to mint grant.');
    operation(() => call('/api/incidents/live', { site: 'casa', category: 'servers' }));
  });
}
if ($('btn-live-bellini')) {
  $('btn-live-bellini').addEventListener('click', () => {
    currentGrant = null;
    setText('grant-status', 'No active grant. Ingest telemetry to mint grant.');
    operation(() => call('/api/incidents/live', { site: 'bellini', category: 'network' }));
  });
}

// Sandbox Create
if ($('create')) {
  $('create').addEventListener('click', () => {
    currentGrant = null;
    setText('grant-status', 'No active grant. Ingest telemetry to mint grant.');
    operation(() => call('/api/incidents', { scenario: $('scenario').value }));
  });
}

// Memory Recall
if ($('btn-recall-memory')) {
  $('btn-recall-memory').addEventListener('click', () => {
    if (!current) return;
    operation(() => call(`/api/incidents/${current.id}/remember`, { query: '' }));
  });
}

// Mint One-Shot Grant
if ($('btn-mint-grant')) {
  $('btn-mint-grant').addEventListener('click', async () => {
    if (!current) return;
    try {
      say('Minting single-use cryptographic grant…');
      const res = await call('/api/grants', { snapshot_digest: current.snapshot_digest, ttl_seconds: 300 });
      currentGrant = res;
      setText('grant-status', `Active Grant: ${res.token.slice(0, 18)}... (Bound to ${res.snapshot_digest.slice(0, 10)}... Expires in 300s)`);
      say('One-shot grant minted. Ready for Meta Muse Spark 1.3.', true);
      disableActions();
    } catch (e) {
      say(e.message);
    }
  });
}

// Meta Muse Spark Reasoning
if ($('btn-meta-analyze')) {
  $('btn-meta-analyze').addEventListener('click', () => {
    if (!current || !currentGrant) return;
    const token = currentGrant.token;
    currentGrant = null; // single-use consumed
    setText('grant-status', 'Grant consumed. Waiting for receipt.');
    operation(() => call(`/api/incidents/${current.id}/analyze`, { mode: 'meta', grant_token: token }));
  });
}

// Standard Lifecycle Handlers
if ($('analyze')) {
  $('analyze').addEventListener('click', () => {
    operation(() => call(`/api/incidents/${current.id}/analyze`, { mode: $('mode').value }));
  });
}
if ($('approve')) {
  $('approve').addEventListener('click', () => {
    operation(() => call(`/api/incidents/${current.id}/approve`, {
      operator: $('operator').value,
      action: current.recommended_action,
    }));
  });
}
if ($('execute')) {
  $('execute').addEventListener('click', () => {
    operation(() => call(`/api/incidents/${current.id}/execute`, {}));
  });
}
if ($('verify')) {
  $('verify').addEventListener('click', () => {
    operation(() => call(`/api/incidents/${current.id}/verify`, {}));
  });
}

// SAM 3.1 Visual Inspection
if ($('btn-run-sam')) {
  $('btn-run-sam').addEventListener('click', async () => {
    const asset = $('sam-asset-select').value;
    try {
      say('Running SAM 3.1 optical inspection on lab hardware…');
      const data = await call(`/api/sam/inspect?asset=${asset}`);
      const box = $('sam-output');
      box.replaceChildren();
      const h = document.createElement('div');
      h.style.fontWeight = 'bold';
      h.style.color = '#75e7d2';
      h.textContent = `👁 ${data.title} (${data.model})`;
      const note = document.createElement('p');
      note.style.fontSize = '12px';
      note.style.color = '#c5d5e6';
      note.textContent = data.analysis_notes;
      box.append(h, note);
      for (const obj of data.detected_objects) {
        const item = document.createElement('div');
        item.className = 'sam-detection';
        item.innerHTML = `<span>[${Math.round(obj.confidence * 100)}% CONFIDENCE]</span> ${obj.label} — <em>${obj.status}</em> <small style="color:#71879e;display:block;">bbox: [${obj.bbox.join(', ')}]</small>`;
        box.append(item);
      }
      say('SAM 3.1 lab inspection complete.', true);
    } catch (e) {
      say(e.message);
    }
  });
}

// JSON Evidence Download
if ($('download')) {
  $('download').addEventListener('click', async () => {
    if (!current) return;
    try {
      const data = await call(`/api/incidents/${current.id}/evidence`);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `inneros-evidence-${current.id.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      say('Complete tamper-evident evidence exported as JSON.', true);
    } catch (e) {
      say(e.message);
    }
  });
}

// Initialize
refresh().catch((e) => say(`Server unavailable: ${e.message}`));
renderCurrent();
