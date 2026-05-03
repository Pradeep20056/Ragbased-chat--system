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

  // Determine page badge label
  const pageLabel = (chunk.page !== undefined && chunk.page !== null && chunk.page !== 'N/A')
    ? `Page ${chunk.page}` : 'N/A';

  // Truncate source filename for display
  const srcShort = chunk.source.length > 32
    ? '…' + chunk.source.slice(-30) : chunk.source;

  // Char count display
  const charCount = chunk.chars ? `${chunk.chars.toLocaleString()} chars` : '';

  // Content preview (first 280 chars)
  const previewLen = 280;
  const fullText   = chunk.content.trim();
  const isLong     = fullText.length > previewLen;
  const preview    = isLong ? fullText.slice(0, previewLen) + '…' : fullText;

  const chunkId = `chunk-${chunk.index}-${idx}`;

  card.innerHTML = `
    <div class="chunk-header">
      <div class="chunk-header-left">
        <span class="chunk-rank">#${chunk.index}</span>
        <div class="chunk-meta-group">
          <span class="chunk-page-badge" title="PDF page number">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            ${pageLabel}
          </span>
          <span class="chunk-file" title="${chunk.source}">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            ${srcShort}
          </span>
          ${charCount ? `<span class="chunk-chars">${charCount}</span>` : ''}
        </div>
      </div>
      <div class="chunk-header-right">
        <button class="chunk-copy-btn" title="Copy chunk text" onclick="copyChunk('${chunkId}')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          Copy
        </button>
      </div>
    </div>

    <div class="chunk-content" id="${chunkId}">${escHtml(fullText)}</div>

    ${isLong ? `
    <div class="chunk-toggle-row">
      <button class="chunk-toggle-btn" onclick="toggleChunk(this, '${chunkId}', ${JSON.stringify(preview).replace(/"/g, '&quot;')}, ${JSON.stringify(fullText).replace(/"/g, '&quot;')})">
        <svg class="toggle-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        Show less
      </button>
    </div>
    ` : ''}
  `;

  // Start collapsed if long
  if (isLong) {
    const contentEl = card.querySelector(`#${chunkId}`);
    contentEl.textContent = preview;
    const toggleBtn = card.querySelector('.chunk-toggle-btn');
    if (toggleBtn) {
      toggleBtn.querySelector('.toggle-icon').style.transform = 'rotate(-90deg)';
      toggleBtn.childNodes[1].textContent = ' Show more';
    }
  }

  container.appendChild(card);
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function toggleChunk(btn, id, preview, full) {
  const el = document.getElementById(id);
  const icon = btn.querySelector('.toggle-icon');
  if (el.dataset.expanded === 'true') {
    el.textContent = preview;
    el.dataset.expanded = 'false';
    icon.style.transform = 'rotate(-90deg)';
    btn.childNodes[1].textContent = ' Show more';
  } else {
    el.textContent = full;
    el.dataset.expanded = 'true';
    icon.style.transform = 'rotate(0deg)';
    btn.childNodes[1].textContent = ' Show less';
  }
}

async function copyChunk(id) {
  const el = document.getElementById(id);
  if (!el) return;
  try {
    await navigator.clipboard.writeText(el.textContent);
    // Flash feedback
    const btn = el.closest('.chunk-card').querySelector('.chunk-copy-btn');
    btn.textContent = '✓ Copied';
    btn.style.color = 'var(--green, #22c55e)';
    setTimeout(() => {
      btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
      btn.style.color = '';
    }, 1800);
  } catch {}
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
