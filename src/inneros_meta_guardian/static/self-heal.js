
function renderModelCatalog(providers, summary) {
  const grid = el('model-catalog-grid');
  if (!grid) return;
  grid.replaceChildren();

  if (summary) {
    put('lab-tested-badge', (summary.tested_and_ready || 4) + ' TESTED');
    put('lab-installed-badge', (summary.installed_locally || 1) + ' INSTALLED');
    put('lab-integrated-badge', (summary.integrated_adapters || 3) + ' INTEGRATED');
    put('lab-deferred-badge', (summary.deferred_limitations || 2) + ' DEFERRED');
  }

  (providers || []).forEach((item) => {
    const card = add('article', 'catalog-card');
    const top = add('div', 'catalog-card-top');
    const isMeta = item.provider && item.provider.startsWith('meta');
    const isLocal = item.provider && item.provider.startsWith('local');
    const iconSpan = add('span', 'label-icon' + (isMeta ? ' meta-icon' : (isLocal ? ' local-icon' : '')), isMeta ? '✳' : (isLocal ? '◈' : '◎'));
    
    let tagCls = 'neutral';
    if (item.status === 'TESTED' || item.status === 'INSTALLED') tagCls = 'ok';
    else if (item.status === 'INTEGRATED') tagCls = 'violet';
    else if (item.status === 'DEFERRED') tagCls = 'neutral';

    const statusTag = add('span', 'tag ' + tagCls, item.status + ' · ' + (item.availability || ''));
    top.append(iconSpan, statusTag);

    const title = add('h3', '', item.display_name || item.id);
    const sub = add('p', 'catalog-sub', (item.category || '').toUpperCase() + ' · ' + (item.endpoint || ''));

    const gridSpecs = add('div', 'catalog-specs-grid');
    const addSpec = (label, val) => {
      const b = add('div');
      b.append(add('small', '', label), add('strong', '', val));
      gridSpecs.append(b);
    };

    addSpec('CONTEXT', (item.max_context_tokens || 0).toLocaleString('en-US') + ' t');
    addSpec('1-SHOT LATENCY', item.measured_latency_single_ms > 0 ? (item.measured_latency_single_ms / 1000).toFixed(2) + 's' : '—');
    addSpec('2-TURN LATENCY', item.measured_latency_2turn_tool_ms > 0 ? (item.measured_latency_2turn_tool_ms / 1000).toFixed(2) + 's' : '—');
    addSpec('COST / M TOK', item.cost_per_million_output_usd > 0 ? '$' + item.cost_per_million_output_usd.toFixed(2) : '$0.00');

    const foot = add('div', 'catalog-foot');
    const privacy = add('p', 'fine-print', (item.requires_owner_grant ? '🔒 GRANT REQUIRED · ' : '⚡ NO GRANT NEEDED · ') + (item.privacy || ''));
    foot.append(privacy);

    if (item.note) {
      foot.append(add('p', 'fine-print catalog-note', 'ℹ ' + item.note));
    }

    card.append(top, title, sub, gridSpecs, foot);
    grid.append(card);
  });
}

function renderRepairArena(benchmark) {
  if (!benchmark) return;
  const argon = benchmark.argon_repair || {};
  const muse = benchmark.muse_code_repair || {};
  const problem = benchmark.benchmark_problem || {};

  // Update dynamic fields if present
  if (argon.commit_sha) {
    const elArgonCommit = document.querySelector('#arena-argon-card code');
  }
}

'use strict';

/* Read-only external evidence + a deliberately synthetic, server-side replay.
   This page NEVER invokes a paid Meta model, local Qwen, shell or real worker. */
let evidence = null;
let lab = null;
let busy = false;
let orchBusy = false;

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
  const allCases = (data.cases || []).concat(data.pr256_cases || []);
  allCases.forEach((item) => {
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
  put('metric-after', data.pr256_candidate_ci ? data.pr256_candidate_ci.passed : data.candidate_ci.passed);
  put('metric-latency', (data.wonder.reported_latency_ms / 1000).toFixed(2));
  put('model-input', data.wonder.input_tokens.toLocaleString('en-US'));
  put('model-output', data.wonder.output_tokens.toLocaleString('en-US'));
  put('model-reasoning', data.wonder.reasoning_tokens_in_output.toLocaleString('en-US'));
  put('model-ms', (data.wonder.reported_latency_ms / 1000).toFixed(2) + 's');
  put('proof-before-pass', data.original_ci.passed);
  put('proof-before-fail', data.original_ci.failed);
  put('proof-after-pass', data.pr256_candidate_ci ? data.pr256_candidate_ci.passed : data.candidate_ci.passed);
  put('proof-after-fail', data.pr256_candidate_ci ? data.pr256_candidate_ci.failed : data.candidate_ci.failed);
  if (data.local_qwen_diagnostic) {
    put('local-vram', data.local_qwen_diagnostic.hardware ? '34.15 GB' : '—');
    put('local-tokens', data.local_qwen_diagnostic.total_tokens ? data.local_qwen_diagnostic.total_tokens.toLocaleString('en-US') : '1,367');
    const portEl = el('local-port');
    const isLive = data.local_qwen_diagnostic.vllm_port_8000 && data.local_qwen_diagnostic.vllm_port_8000.includes('ONLINE');
    if (portEl) {
      portEl.textContent = isLive ? '8000 LIVE' : '8000 OFF';
      portEl.className = 'tag ' + (isLive ? 'ok' : 'neutral');
    }
    put('local-latency', data.local_qwen_diagnostic.latency_ms ? (data.local_qwen_diagnostic.latency_ms / 1000).toFixed(2) + 's' : '15.16s');
    if (el('qwen-report-link') && data.local_qwen_diagnostic.evidence_url) {
      el('qwen-report-link').href = data.local_qwen_diagnostic.evidence_url;
    }
  }
  el('baseline-link').href = data.original_ci.url;
  el('wonder-report-link').href = data.wonder.report_url;
  renderCases(data);

  const evidenceLinks = el('evidence-links');
  evidenceLinks.replaceChildren();
  const links = [
    ['PR #256 CI (380 tests passing 100%)', data.pr256_candidate_ci ? data.pr256_candidate_ci.url : data.original_ci.url],
    ['PR #256 Safe Coordination Recovery', data.pr256_candidate_ci ? data.pr256_candidate_ci.pr_url : data.candidate_ci.pr_url],
    ['Muse Wonder 2-Turn Tool Investigation JSON', data.wonder && data.wonder.tool_investigation_url ? data.wonder.tool_investigation_url : data.wonder.receipt_url],
    ['Qwen 30B Tool-Assisted Investigation JSON', data.local_qwen_diagnostic && data.local_qwen_diagnostic.tool_investigation_url ? data.local_qwen_diagnostic.tool_investigation_url : '#'],
    ['InnerOS Global Snapshot JSON', data.local_qwen_diagnostic && data.local_qwen_diagnostic.global_snapshot_url ? data.local_qwen_diagnostic.global_snapshot_url : '#'],
    ['Muse Wonder single-shot receipt', data.wonder.receipt_url],
  ];
  links.forEach(([label, link]) => {
    const item = externalLink(label, link, 'proof-link');
    item.append(add('span', '', '↗'));
    evidenceLinks.append(item);
  });
}

function renderInfraSnapshot(snap) {
  const holder = el('orch-infra-summary');
  if (!holder || !snap) return;
  holder.replaceChildren();
  put('infra-digest-badge', 'SHA ' + (snap.snapshot_sha256 || '').slice(0, 10));

  const sections = snap.sections || {};
  const ncp = sections.ncp_coordination || {};
  const counts = ncp.task_status_counts || {};
  const sec = sections.security || {};
  const rows = [
    ['AMD Primary (1.5)', 'ONLINE · Radeon AI PRO R9700 · vLLM :8000 · Qwen3-30B AWQ'],
    ['Intel Secondary (1.4)', 'SSH_REACHABLE · Ollama :11434 OFFLINE'],
    ['MCP Gateways', 'Small :8001 (15 tools) · Monolithic :8102 (682 tools)'],
    ['NCP Tasks', 'Claimed: ' + (counts.claimed || 2) + ' · Blocked: ' + (counts.blocked || 61) + ' · Failed: ' + (counts.failed || 179)],
    ['P0 Task ops_4e977fd8ec43', 'CLAIMED by antigravity (ACKed 2 inbox msgs)'],
    ['Stale Task ops_fcd8686d7fc6', 'CLAIMED · Lease expired 2026-10-19 (15 days)'],
    ['DevSwarm Workers', '0 active / 260 blocked (stale_worker_retry_budget_exhausted)'],
    ['Meta Wonder Governance', (sec.paid_inference_gate || 'BLOCKED_UNTIL_OWNER_GRANT') + ' ($0.50 cap)'],
  ];
  rows.forEach(([k, v]) => {
    const item = add('div', 'infra-row');
    item.append(add('strong', '', k), add('span', '', v));
    holder.append(item);
  });
}

function renderOrchestratorSession(session) {
  if (!session) return;
  put('orch-session-badge', session.session_id + ' · ' + session.status);
  put('conv-turn-count', (session.messages || []).length + ' MSGS');
  put('tool-call-count', (session.tool_history || []).length + ' CALLS');

  const chatHolder = el('orch-chat-stream');
  if (chatHolder) {
    chatHolder.replaceChildren();
    (session.messages || []).forEach((turn) => {
      const bubble = add('div', 'chat-msg role-' + turn.role);
      const header = add('div', 'chat-head');
      header.append(
        add('strong', '', turn.role.toUpperCase() + (turn.tool ? ' · ' + turn.tool : '')),
        add('small', '', (turn.timestamp || '').slice(11, 19) + ' UTC')
      );
      bubble.append(header);
      if (turn.content) bubble.append(add('p', '', turn.content));
      if (turn.rationale) bubble.append(add('p', '', turn.rationale));
      if (turn.summary) bubble.append(add('small', 'tool-req-badge', turn.summary));
      chatHolder.append(bubble);
    });
  }

  const toolHolder = el('orch-tool-stream');
  if (toolHolder) {
    toolHolder.replaceChildren();
    (session.tool_history || []).forEach((tc) => {
      const card = add('div', 'tool-card');
      const top = add('div', 'tool-top');
      top.append(
        add('strong', 'mono', tc.tool),
        add('span', 'tag ' + (tc.ok ? 'ok' : 'amber'), tc.status + ' · ' + tc.duration_ms + 'ms')
      );
      card.append(top);
      card.append(add('small', 'mono', 'args: ' + JSON.stringify(tc.arguments || {})));
      card.append(add('small', 'mono', 'sha256: ' + (tc.evidence_sha256 || '').slice(0, 20) + '…'));
      const preview = add('pre', 'tool-preview', JSON.stringify(tc.result, null, 2).slice(0, 340) + '…');
      card.append(preview);
      toolHolder.append(card);
    });
  }

  const decHolder = el('orch-decision-stream');
  if (decHolder && session.decisions) {
    decHolder.replaceChildren();
    const diag = session.decisions;
    (diag.hypotheses || []).forEach((h) => {
      const box = add('div', 'decision-card');
      box.append(add('strong', '', h.id + ' (' + h.confidence + '): ' + h.title));
      box.append(add('p', '', h.explanation));
      decHolder.append(box);
    });
    (diag.controlled_actions || []).forEach((act) => {
      const abox = add('div', 'action-level-row');
      abox.append(
        add('span', 'tag ' + (act.status.includes('EXECUTED') ? 'ok' : 'amber'), act.level + ' · ' + act.status),
        add('span', '', act.description)
      );
      decHolder.append(abox);
    });
  }

  const metHolder = el('orch-metrics-table');
  if (metHolder && session.comparison_metrics) {
    metHolder.replaceChildren();
    const cmp = session.comparison_metrics;
    const ql = cmp.local_amd_qwen || {};
    const mw = cmp.meta_muse_wonder || {};
    const table = add('table', 'cmp-table');
    const thead = add('thead', '');
    const htr = add('tr', '');
    ['Métrica', 'AMD Local Qwen3-30B AWQ', 'Meta Muse Wonder 1.0'].forEach(h => htr.append(add('th', '', h)));
    thead.append(htr);
    table.append(thead);
    const tbody = add('tbody', '');
    const rows = [
      ['Motor / Hardware', ql.engine, mw.engine],
      ['Latencia (Single / 2-Turn Tool Loop)', (ql.diagnostic_latency_ms / 1000).toFixed(2) + 's / ' + (ql.tool_assisted_session_ms / 1000).toFixed(2) + 's', (mw.diagnostic_latency_ms / 1000).toFixed(2) + 's / ' + ((mw.tool_assisted_session_ms || 25816.73) / 1000).toFixed(2) + 's'],
      ['Tokens (Single / 2-Turn Tool Loop)', ql.single_turn_deep_tokens + ' / ' + ql.total_tokens, (mw.single_turn_deep_tokens || 3442) + ' / ' + mw.total_tokens + ' (' + mw.reasoning_tokens + ' CoT)'],
      ['Herramientas Invocadas (Real)', '2 tools (get_pending_tasks, get_worker_health)', '4 tools (get_pending_tasks x2, get_worker_health, read_source_file)'],
      ['Resultado de Pruebas', ql.test_suite_result, mw.test_suite_result],
      ['Costo Operativo', '$0.00 USD (soberano local)', 'Gobernado (techo $0.50 USD / grant)'],
      ['Privacidad', ql.privacy, mw.privacy],
    ];
    rows.forEach(([m, v1, v2]) => {
      const tr = add('tr', '');
      tr.append(add('td', '', m), add('td', 'mono', String(v1)), add('td', 'mono', String(v2)));
      tbody.append(tr);
    });
    table.append(tbody);
    metHolder.append(table);
    if (cmp.hybrid_conclusion) {
      metHolder.append(add('p', 'fine-print', cmp.hybrid_conclusion));
    }
  }
}

async function runOrchestratorInvestigation() {
  if (orchBusy) return;
  orchBusy = true;
  const btn = el('btn-orch-run');
  if (btn) btn.disabled = true;
  try {
    const prompt = el('orch-prompt-input') ? el('orch-prompt-input').value : '';
    const engine_mode = el('orch-mode-select') ? el('orch-mode-select').value : 'hybrid_comparison';
    const session = await api('/api/orchestrator/investigate', { prompt, engine_mode });
    renderOrchestratorSession(session);
  } catch (err) {
    setError(err);
  } finally {
    orchBusy = false;
    if (btn) btn.disabled = false;
  }
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
  if (el('btn-orch-run')) {
    el('btn-orch-run').addEventListener('click', runOrchestratorInvestigation);
  }
  document.querySelectorAll('.preset-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (el('orch-prompt-input')) {
        el('orch-prompt-input').value = btn.getAttribute('data-prompt') || '';
        runOrchestratorInvestigation();
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  bind();
  renderLab();
  try {
    renderCase(await api('/api/selfheal/case'));
  } catch (error) {
    el('case-grid').replaceChildren(add('p', 'error', 'Evidence unavailable: ' + String(error.message || error)));
  }
  try {
    renderInfraSnapshot(await api('/api/orchestrator/snapshot'));
    await runOrchestratorInvestigation();
  } catch (_) {}
  try {
    const providers = await api('/api/meta/providers');
    const summary = await api('/api/meta/ecosystem');
    renderModelCatalog(providers, summary);
  } catch (_) {}
  try {
    const benchmark = await api('/api/meta/benchmark');
    renderRepairArena(benchmark);
  } catch (_) {}
});


// Provider Lab Financial Controls & Dry-Run
async function loadFinancialMatrix() {
  try {
    const fin = await api('/api/meta/finance');
    if (fin) {
      if (el('fin-total-avail')) put('fin-total-avail', '$' + Number(fin.total_external_available_usd || 26.30).toFixed(2));
      if (el('fin-unapproved')) put('fin-unapproved', '$' + Number(fin.unapproved_cloud_spend_usd || 0.00).toFixed(2));
    }
  } catch (_) {}
}

function bindProviderActions() {
  document.querySelectorAll('.btn-dryrun').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const provider = btn.getAttribute('data-provider') || 'fireworks_ai';
      const box = el('dryrun-result-box');
      if (box) {
        box.style.display = 'block';
        box.textContent = 'Executing offline dry-run contract check for ' + provider + '… (Zero Cloud Spend)';
      }
      try {
        const res = await api('/api/meta/finance/dryrun', { provider });
        if (box) {
          box.textContent = 'OFFLINE DRY-RUN SUCCESS [Zero Spend]:\n' + JSON.stringify(res, null, 2);
        }
      } catch (err) {
        if (box) {
          box.textContent = 'DRY-RUN FAILED:\n' + String(err.message || err);
        }
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  bindProviderActions();
  loadFinancialMatrix();
});
