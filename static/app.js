/* ═══════════════════════════════════════════════════════════
   app.js — Tender Evaluation RAG Demo
   ═══════════════════════════════════════════════════════════ */

const API = {
  sections: '/api/sections',
  evaluate: (id) => `/api/evaluate/${id}`,
};

// State
let selectedSection = null;
let isLoading       = false;

// DOM refs
const sectionList     = document.getElementById('sectionList');
const runBtn          = document.getElementById('runBtn');
const runBtnText      = document.getElementById('runBtnText');
const emptyState      = document.getElementById('emptyState');
const loadingState    = document.getElementById('loadingState');
const resultsPane     = document.getElementById('resultsPane');
const errorState      = document.getElementById('errorState');
const fieldsContainer = document.getElementById('fieldsContainer');
const chunksContainer = document.getElementById('chunksContainer');
const statsBar        = document.getElementById('statsBar');
const llmBadge        = document.getElementById('llmBadge');
const llmLabel        = document.getElementById('llmLabel');

// Loading step elements
const loadingSteps = [
  document.getElementById('ls1'),
  document.getElementById('ls2'),
  document.getElementById('ls3'),
  document.getElementById('ls4'),
];
let stepTimer = null;

/* ── Fetch section list on load ─────────────────────────── */
async function loadSections() {
  try {
    const res  = await fetch(API.sections);
    const data = await res.json();
    renderSections(data);
  } catch (err) {
    sectionList.innerHTML = `<p style="color:var(--red);padding:12px;font-size:.82rem">⚠ Cannot reach API server.<br>Make sure uvicorn is running.</p>`;
  }
}

function renderSections(sections) {
  sectionList.innerHTML = '';
  sections.forEach(sec => {
    const btn = document.createElement('button');
    btn.className    = 'section-btn';
    btn.dataset.id   = sec.id;
    btn.dataset.label= sec.label;
    btn.innerHTML    = `
      <span class="section-badge">${sec.id}</span>
      <span class="section-label">${sec.label.replace(/^\([a-f]\)\s*/, '')}</span>
    `;
    btn.addEventListener('click', () => selectSection(sec, btn));
    sectionList.appendChild(btn);
  });
}

function selectSection(sec, btn) {
  if (isLoading) return;
  selectedSection = sec;
  document.querySelectorAll('.section-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  runBtn.disabled = false;
  runBtnText.textContent = `Run Section (${sec.id.toUpperCase()})`;
}

/* ── Run evaluation ─────────────────────────────────────── */
runBtn.addEventListener('click', () => {
  if (!selectedSection || isLoading) return;
  runEvaluation(selectedSection.id, selectedSection.label);
});

async function runEvaluation(sectionId, sectionLabel) {
  isLoading = true;
  runBtn.disabled = true;
  runBtn.classList.add('loading');
  runBtnText.textContent = 'Evaluating...';
  document.getElementById('loadingTitle').textContent = `Evaluating ${sectionLabel}...`;

  showState('loading');
  startLoadingSteps();

  try {
    const res = await fetch(API.evaluate(sectionId), { method: 'POST' });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    stopLoadingSteps(true);

    // Small delay so user sees "done" state
    setTimeout(() => renderResults(data), 700);

  } catch (err) {
    stopLoadingSteps(false);
    setTimeout(() => showError('Evaluation Failed', err.message), 400);
  } finally {
    isLoading = false;
    runBtn.disabled = false;
    runBtn.classList.remove('loading');
    runBtnText.textContent = selectedSection
      ? `Run Section (${selectedSection.id.toUpperCase()})`
      : 'Select a Section';
  }
}

/* ── Loading step animation ─────────────────────────────── */
function startLoadingSteps() {
  loadingSteps.forEach(el => { el.classList.remove('active','done'); });
  let idx = 0;
  loadingSteps[0].classList.add('active');

  stepTimer = setInterval(() => {
    if (idx < loadingSteps.length - 1) {
      loadingSteps[idx].classList.remove('active');
      loadingSteps[idx].classList.add('done');
      idx++;
      loadingSteps[idx].classList.add('active');
    }
  }, 1800);
}

function stopLoadingSteps(success) {
  clearInterval(stepTimer);
  loadingSteps.forEach((el, i) => {
    el.classList.remove('active');
    if (success) el.classList.add('done');
  });
}

/* ── Render results ─────────────────────────────────────── */
function renderResults(data) {
  showState('results');

  // Stats bar
  document.getElementById('statSection').innerHTML =
    `📋 <strong>${data.section_label}</strong>`;
  document.getElementById('statChunks').innerHTML =
    `📦 <strong>${data.chunks_retrieved}</strong> chunks retrieved`;
  document.getElementById('statFields').innerHTML =
    `🔑 <strong>${Object.keys(data.extracted).length}</strong> fields extracted`;
  document.getElementById('statLlm').innerHTML =
    `🤖 <strong>${data.llm_used}</strong>`;

  // LLM badge
  llmLabel.textContent = data.llm_used;
  llmBadge.style.display = 'block';

  // Render extracted fields
  fieldsContainer.innerHTML = '';
  renderFields(data.extracted, fieldsContainer);

  // Render chunks
  chunksContainer.innerHTML = '';
  data.chunks.forEach((chunk, i) => renderChunk(chunk, i, chunksContainer));
}

function renderFields(obj, container, delay = 0) {
  Object.entries(obj).forEach(([key, val], idx) => {
    const card = document.createElement('div');
    card.className = 'field-card';
    card.style.animationDelay = `${idx * 35}ms`;

    const keyEl = document.createElement('div');
    keyEl.className = 'field-key';
    keyEl.textContent = key.replace(/_/g, ' ');

    const valEl = document.createElement('div');
    valEl.className = 'field-val';

    if (Array.isArray(val)) {
      if (val.length === 0) {
        valEl.textContent = 'None';
        valEl.classList.add('not-found');
      } else {
        valEl.classList.add('is-list');
        val.forEach(item => {
          const li = document.createElement('div');
          li.className = 'field-list-item';
          li.textContent = String(item);
          valEl.appendChild(li);
        });
      }
    } else if (typeof val === 'object' && val !== null) {
      valEl.textContent = JSON.stringify(val, null, 2);
    } else {
      const strVal = String(val);
      valEl.textContent = strVal;
      if (strVal === 'Not Found in Documents' || strVal === '—') {
        valEl.classList.add('not-found');
      } else if (/accepted|qualified|positive|yes|submitted/i.test(strVal)) {
        valEl.classList.add('status-accepted');
      } else if (/rejected|not qualified|negative/i.test(strVal)) {
        valEl.classList.add('status-rejected');
      } else if (/query|under/i.test(strVal)) {
        valEl.classList.add('status-query');
      }
    }

    card.appendChild(keyEl);
    card.appendChild(valEl);
    container.appendChild(card);
  });
}

function renderChunk(chunk, idx, container) {
  const card = document.createElement('div');
  card.className = 'chunk-card';
  card.style.animationDelay = `${idx * 45}ms`;

  const header = document.createElement('div');
  header.className = 'chunk-header';
  header.innerHTML = `
    <span class="chunk-num">${chunk.index}</span>
    <span class="chunk-source" title="${chunk.source}">📄 ${chunk.source}</span>
    <span class="chunk-bidder">${chunk.bidder}</span>
  `;

  const content = document.createElement('div');
  content.className = 'chunk-content';
  content.textContent = chunk.content.trim();

  card.appendChild(header);
  card.appendChild(content);
  container.appendChild(card);
}

/* ── UI state helpers ───────────────────────────────────── */
function showState(state) {
  emptyState.style.display   = 'none';
  loadingState.style.display = 'none';
  resultsPane.style.display  = 'none';
  errorState.style.display   = 'none';

  if (state === 'empty')   { emptyState.style.display   = 'flex'; }
  if (state === 'loading') { loadingState.style.display = 'flex'; }
  if (state === 'results') { resultsPane.style.display  = 'flex'; }
  if (state === 'error')   { errorState.style.display   = 'flex'; }
}

function showError(title, msg) {
  document.getElementById('errorTitle').textContent = title;
  document.getElementById('errorMsg').textContent   = msg;
  showState('error');
}

function resetUI() {
  showState('empty');
  selectedSection = null;
  document.querySelectorAll('.section-btn').forEach(b => b.classList.remove('active'));
  runBtn.disabled = true;
  runBtnText.textContent = 'Select a Section';
  llmBadge.style.display = 'none';
}

/* ── Bootstrap ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  showState('empty');
  loadSections();
});
