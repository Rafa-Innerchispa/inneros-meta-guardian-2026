'use strict';

/* Read-only external evidence + a deliberately synthetic, server-side replay.
   This page NEVER invokes a paid Meta model, local Qwen, shell or real worker. */
let evidence = null;
let lab = null;
let busy = false;

const el = (id) => document.getElementById(id);
const put = (id, value) => { if (el(id)) el(id).textContent = String(value); };

async function api(path, payload) {
  const options = payload === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  };
  const response = await fetch(path, options);
  let result;
  try { result = await response.json(); }
  catch (_) { throw new Error('Server did not return JSON'); }
  if (!response.ok) throw new Error(result.error || 'HTTP ' + response.status);
  return result;
}

function add(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = String(value);
  return node;
}

function externalLink(text, href, cls) {
  const link = add('a', cls || 'text-link', text);
  link.href = href;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  return link;
}

function renderCases(data) {
  const holder = el('case-grid');
  holder.replaceChildren();
  data.cases.forEach((item) => {
    const card = add('article', 'case-card');
    const head = add('div', 'case-top');
    const label = item.truth === 'SOURCE_CODE_AND_CI_VERIFIED' ? 'CODE + CI' : 'TEST CONTRACT';
    head.append(add('span', 'case-id', item.id), add('span', 'tag ' +
      (label === 'CODE + CI' ? 'ok' : 'amber'), label));
    card.append(head, add('h3', '', item.name));
    card.append(add('p', 'component', item.component));
    card.append(add('p', '', item.symptom));
    card.append(add('p', 'fix-note', item.fix));
    const small = add('p', 'fine-print', item.verification);
    small.style.marginTop = '11px';
    card.append(small);
    holder.append(card);
  });
}

function renderCase(data) {
  evidence = data;
  put('metric-open', data.live_coordination_snapshot.open_records);
  put('metric-before', data.original_ci.failed);
  put('metric-after', data.candidate_ci.passed);
  put('metric-latency', (data.wonder.reported_latency_ms / 1000).toFixed(2));
  put('model-input', data.wonder.input_tokens.toLocaleString('en-US'));
  put('model-output', data.wonder.output_tokens.toLocaleString('en-US'));
  put('model-reasoning', data.wonder.reasoning_tokens_in_output.toLocaleString('en-US'));
  put('model-ms', (data.wonder.reported_latency_ms / 1000).toFixed(2) + 's');
  put('proof-before-pass', data.original_ci.passed);
  put('proof-before-fail', data.original_ci.failed);
  put('proof-after-pass', data.candidate_ci.passed);
  put('proof-after-fail', data.candidate_ci.failed);
  el('baseline-link').href = data.original_ci.url;
  el('wonder-report-link').href = data.wonder.report_url;
  renderCases(data);

  const evidenceLinks = el('evidence-links');
  evidenceLinks.replaceChildren();
  [
    ['Original failing CI', data.original_ci.url],
    ['Clean candidate CI', data.candidate_ci.url],
    ['Muse Wonder receipt', data.wonder.receipt_url],
    ['Review repair PR', data.candidate_ci.pr_url],
    ['Approval hardening PR', data.release.auth_pr],
  ].forEach(([label, link]) => {
    const item = externalLink(label, link, 'proof-link');
    item.append(add('span', '', '↗'));
    evidenceLinks.append(item);
  });
}

const STATES = ['observed','diagnosed','reasoned','approved','patched','verified'];
const ACTIONS = [
  ['btn-lab-diagnose', 'observed'],
  ['btn-lab-replay', 'diagnosed'],
  ['btn-lab-ack', 'reasoned'],
  ['btn-lab-patch', 'approved'],
  ['btn-lab-verify', 'patched'],
];

function renderLab() {
  const state = lab ? lab.status : 'not_started';
  put('lab-status', state.replace(/_/g, ' ').toUpperCase());
  const badge = el('lab-status');
  badge.className = 'tag ' + (state === 'verified' ? 'ok' : 'neutral');
  el('btn-lab-start').disabled = busy;
  el('btn-lab-export').disabled = busy || !lab;
  for (const [id, target] of ACTIONS) el(id).disabled = busy || state !== target;
  const position = STATES.indexOf(state);
  document.querySelectorAll('#progress-track span').forEach((item, index) => {
    item.className = index < position ? 'done' : index === position ? 'active' : '';
  });
  if (!lab) {
    put('lab-state', 'Create the lab incident to begin a new, isolated demonstration. Nothing touches production or a paid provider.');
    put('audit-state', 'SHA-256 chain: waiting');
    put('audit-count', '0');
    return;
  }

  const f = lab.fixture;
  const lines = [
    'SANDBOX ' + lab.id + '  •  ' + lab.source_truth,
    'Task: ' + f.task_status + '   /   Lease: ' + (f.lease_expired ? 'EXPIRED' : 'VALID'),
    'Worker: ' + (f.worker_running ? 'RUNNING' : 'NOT RUNNING'),
  ];
  if (lab.diagnosis) lines.push('Diagnosis: ' + lab.diagnosis.suspected_cause + ' [' + lab.diagnosis.method + ']');
  if (lab.wonder) lines.push('Muse: HISTORICAL RECEIPT REPLAYED. No Meta request sent.');
  if (lab.approval) lines.push('Authority: LAB ACK ONLY. No owner grant, no device access.');
  if (lab.patch) lines.push('Patch: IN-MEMORY only, zero changed production files.');
  if (lab.verification) lines.push('Verification: ' +
    (lab.verification.passed ? 'PASS (synthetic independent readback)' : 'FAIL SAFE'));
  put('lab-state', lines.join('\n'));
  put('audit-count', lab.events.length);
  const list = el('lab-events');
  list.replaceChildren();
  lab.events.slice().reverse().forEach((event) => {
    const item = add('li', '');
    item.append(add('strong', '', event.sequence + ' / ' + event.phase));
    item.append(add('small', '', (event.recorded_at || '').slice(11, 23) + ' UTC'));
    item.append(add('small', '', 'SHA-256 ' + event.hash.slice(0, 18) + '…'));
    list.append(item);
  });
  put('audit-state', lab.audit.valid
    ? 'Chain VALID · ' + lab.audit.events + ' events'
    : 'Chain FAILED · independent review required');
}

function setError(error) {
  const node = el('lab-error');
  if (!node) return;
  if (!error) { node.hidden = true; node.textContent = ''; return; }
  node.hidden = false;
  node.textContent = String(error.message || error);
}

async function doLab(action, actor) {
  if (busy) return;
  busy = true;
  setError(null);
  renderLab();
  try {
    if (action === 'start') lab = await api('/api/selfheal/labs', {scenario: 'stale_agent_claim'});
    else {
      if (!lab) throw new Error('Start a sandbox session first');
      lab = await api('/api/selfheal/labs/' + encodeURIComponent(lab.id) + '/transition', {
        action, actor: actor || ''
      });
    }
  } catch (error) {
    setError(error);
  } finally {
    busy = false;
    renderLab();
  }
}

async function exportAudit() {
  if (!lab || busy) return;
  busy = true;
  renderLab();
  try {
    const record = await api('/api/selfheal/labs/' + encodeURIComponent(lab.id) + '/evidence');
    const blob = new Blob([JSON.stringify(record, null, 2)], {type: 'application/json'});
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = 'inneros-selfheal-SANDBOX-' + lab.id + '.json';
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    setError(error);
  } finally {
    busy = false;
    renderLab();
  }
}

function bind() {
  el('btn-lab-start').addEventListener('click', () => doLab('start'));
  el('btn-lab-diagnose').addEventListener('click', () => doLab('diagnose'));
  el('btn-lab-replay').addEventListener('click', () => doLab('replay_wonder'));
  el('btn-lab-ack').addEventListener('click', () => doLab('acknowledge_lab', el('lab-actor').value));
  el('btn-lab-patch').addEventListener('click', () => doLab('apply_virtual_patch'));
  el('btn-lab-verify').addEventListener('click', () => doLab('verify'));
  el('btn-lab-export').addEventListener('click', exportAudit);
}

document.addEventListener('DOMContentLoaded', async () => {
  bind();
  renderLab();
  try {
    renderCase(await api('/api/selfheal/case'));
  } catch (error) {
    el('case-grid').replaceChildren(add('p', 'error', 'Evidence unavailable: ' + String(error.message || error)));
    // No fake fallback data or invented metrics.
  }
});
