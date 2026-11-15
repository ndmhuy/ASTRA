const $ = id => document.getElementById(id);
let subjects = {}, searchSequence = 0, existingCorpus = false;
const label = key => subjects[key]?.[0] || key;
// Source text is always rendered as text, including imported Markdown/HTML.
const node = (tag, className, text) => {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
};
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || 'Request failed.');
  return payload;
}
async function openDocument(id) {
  try {
    const d = await api('/api/documents/' + encodeURIComponent(id));
    $('doc-title').textContent = d.title;
    $('doc-meta').textContent = `${label(d.subject)} · ${d.grade ? 'Grade ' + d.grade : 'Grade mapping unknown'} · ${d.chapter ? 'Chapter ' + d.chapter : 'Chapter mapping unknown'} · ${d.edition} · ${d.approval_status} · ${d.evidence_class}`;
    $('doc-text').textContent = d.content;
    const {content, ...metadata} = d;
    $('doc-json').textContent = JSON.stringify(metadata, null, 2);
    $('document-dialog').showModal();
  } catch (error) { showNotice('Could not open source', error.message); }
}
async function loadCollection() {
  const data = await api('/api/collection'); subjects = data.subjects;
  existingCorpus = Boolean(data.corpus_info);
  $('collection-kind').parentElement.hidden = !existingCorpus;
  $('add').hidden = existingCorpus;
  if (existingCorpus) {
    const info = data.corpus_info;
    $('corpus-note').textContent = `${info.curriculum_rows} curriculum rows · ${info.exam_papers} searchable papers · ${info.excluded_papers} excluded papers. Internal prototype; draft/OCR status retained.`;
    document.querySelector('footer').textContent = `Corpus snapshot ${info.snapshot.slice(0, 12)} · Knowledge-first unified search across curriculum units and exam transcriptions.`;
    $('query').value = 'Dao động điều hòa con lắc lò xo';
  }
  $('count').textContent = data.documents.length;
  const selectedEdition = $('edition').value;
  $('edition').replaceChildren(new Option('Auto', ''));
  for (const edition of data.editions) $('edition').add(new Option(edition, edition));
  $('edition').value = data.editions.includes(selectedEdition) ? selectedEdition : '';
  $('collection').replaceChildren();
  for (const d of data.documents) {
    const button = node('button', 'source-link', d.title);
    button.append(node('small', '', `${label(d.subject)}${d.grade ? ' · Lớp ' + d.grade : ' · Grade unknown'}${d.chapter ? ' · Ch. ' + d.chapter : ''} · ${d.approval_status}`));
    button.addEventListener('click', () => openDocument(d.document_id));
    $('collection').append(button);
  }
  if (!$('import-subject').options.length) {
    for (const [key, aliases] of Object.entries(subjects)) { const o = node('option', '', aliases[0]); o.value = key; $('import-subject').append(o); }
    $('import-subject').value = 'vat-li';
  }
}
function showNotice(title, message) {
  const box = node('div', 'notice');
  box.append(node('strong', '', title), node('span', '', message));
  $('notice').replaceChildren(box);
}
function formatScoreBadge(d, mode) {
  const bm25 = (d.bm25_score ?? d.relevance_score ?? 0).toFixed(2);
  const emb = (d.embedding_score ?? 0).toFixed(2);
  const rel = (d.relevance_score ?? 0).toFixed(2);
  if (mode === 'bm25') return `BM25 score ${bm25} · Cosine ${emb}`;
  if (mode === 'embedding') return `Cosine ${emb} · BM25 ${bm25}`;
  return `Hybrid ${rel} · BM25 ${bm25} · Cosine ${emb}`;
}
function renderScopeTags(scope, mode) {
  $('scope').replaceChildren();
  if (!scope) return;
  const modeTag = {hybrid: 'Mode: Hybrid RRF', bm25: 'Mode: BM25-v2', embedding: 'Mode: Embedding Cosine', compare: 'Mode: 3-Way Comparison'}[mode] || `Mode: ${mode}`;
  const kwText = scope.keywords?.length ? `Keywords: ${scope.keywords.slice(0, 8).join(', ')}` : 'Knowledge search';
  for (const text of [modeTag, 'Knowledge search', kwText]) {
    $('scope').append(node('span', 'tag', text));
  }
}
async function search(event) {
  event?.preventDefault();
  const sequence = ++searchSequence;
  const mode = $('retrieval-mode').value || 'hybrid';
  $('search-button').disabled = true; $('search-button').textContent = 'Retrieving…'; $('results-section').setAttribute('aria-busy', 'true');
  $('results').replaceChildren(); $('compare-results').replaceChildren(); $('compare-results').hidden = true;
  $('scope').replaceChildren(); $('notice').replaceChildren(); $('timing').textContent = '';
  $('json').textContent = 'Retrieving…';
  try {
    const payload = {query_text: $('query').value, top_k: Number($('top-k').value), edition: $('edition').value || null, mode};
    if (existingCorpus) payload.collection = $('collection-kind').value;
    const data = await api('/api/search', payload);
    if (sequence !== searchSequence) return;
    $('json').textContent = JSON.stringify(data, null, 2);
    $('timing').textContent = `${data.documents.length} results · ${data.collection_size} sources · ${data.elapsed_ms} ms`;
    renderScopeTags(data.resolved_scope, data.mode || mode);
    if (data.status !== 'success') {
      const hints = {
        no_documents_in_scope: existingCorpus ? 'Try another collection filter or inspect the source collection.' : 'No approved documents are available in the collection.',
        missing_keywords: 'Enter at least one knowledge or topic keyword (for example “dao động điều hòa” or “định luật Ohm”).',
        no_relevant_match: 'No matching passages found. Try another keyword or switch to Hybrid / Embedding mode.'
      };
      showNotice('No documents retrieved', data.gaps.map(g => hints[g.code] || g.message).join(' '));
      return;
    }
    data.documents.forEach((d, i) => {
      const card = node('article', 'result-card'), top = node('div', 'card-top');
      const metaParts = [label(d.subject)];
      if (d.grade) metaParts.push(`Lớp ${d.grade}`);
      if (d.chapter) metaParts.push(`Ch. ${d.chapter}`);
      const sourceLabel = d.evidence_class === 'synthetic' ? `Demo note · ${metaParts.join(' · ')}` : `${d.content_kind || 'knowledge'} · ${metaParts.join(' · ')} · ${d.approval_status}`;
      const qBadge = d.passage_label ? ` · ${d.passage_label}` : '';
      top.append(node('span', '', `${i + 1}. ${sourceLabel}${qBadge}`), node('span', 'score-pill', formatScoreBadge(d, data.mode || mode)));
      const bottom = node('div', 'card-bottom');
      bottom.append(node('span', '', `${d.source_id} · characters ${d.excerpt_start}–${d.excerpt_end}`));
      const button = node('button', 'text-button', 'Read full document ↗');
      button.addEventListener('click', () => openDocument(d.document_id));
      bottom.append(button);
      card.append(top, node('h3', '', d.title), node('p', '', d.excerpt), bottom);
      $('results').append(card);
    });
  } catch (error) { if (sequence === searchSequence) { showNotice('Retrieval failed', error.message); $('json').textContent = error.message; } }
  finally { if (sequence === searchSequence) { $('search-button').disabled = false; $('search-button').textContent = 'Retrieve documents'; $('results-section').setAttribute('aria-busy', 'false'); } }
}
async function compareModes() {
  const sequence = ++searchSequence;
  $('compare-button').disabled = true; $('compare-button').textContent = 'Comparing…';
  $('results').replaceChildren(); $('compare-results').replaceChildren(); $('compare-results').hidden = false;
  $('scope').replaceChildren(); $('notice').replaceChildren(); $('timing').textContent = '';
  try {
    const payload = {query_text: $('query').value, top_k: Number($('top-k').value), edition: $('edition').value || null};
    if (existingCorpus) payload.collection = $('collection-kind').value;
    const data = await api('/api/compare', payload);
    if (sequence !== searchSequence) return;
    $('json').textContent = JSON.stringify(data, null, 2);
    $('timing').textContent = `3-mode comparison · ${data.shared_top_k_count}/${data.unique_top_k_count} shared top hits · ${data.elapsed_ms} ms`;
    const firstScope = data.modes.hybrid?.resolved_scope || data.modes.bm25?.resolved_scope;
    renderScopeTags(firstScope, 'compare');
    const grid = node('div', 'compare-grid');
    const titles = {hybrid: 'Hybrid (RRF + Blend)', bm25: 'BM25-v2 (Lexical)', embedding: 'Embedding (Cosine)'};
    for (const mode of ['hybrid', 'bm25', 'embedding']) {
      const mRes = data.modes[mode];
      const col = node('div', 'compare-col');
      const head = node('div', 'compare-head');
      head.append(node('strong', '', titles[mode]), node('span', 'muted small', `${mRes.documents.length} hits · ${mRes.elapsed_ms} ms`));
      col.append(head);
      if (mRes.status !== 'success') {
        col.append(node('p', 'muted small', mRes.gaps.map(g => g.code + ': ' + g.message).join(' ')));
      } else {
        mRes.documents.forEach((d, idx) => {
          const item = node('div', 'compare-item');
          const meta = node('div', 'card-top');
          meta.append(
            node('span', '', `#${idx + 1}${d.passage_label ? ' · ' + d.passage_label : ''}`),
            node('span', 'score-pill', formatScoreBadge(d, mode))
          );
          const titleBtn = node('button', 'text-button compare-title', d.title);
          titleBtn.addEventListener('click', () => openDocument(d.document_id));
          const snip = node('p', 'small', d.excerpt.slice(0, 160) + (d.excerpt.length > 160 ? '…' : ''));
          item.append(meta, titleBtn, snip);
          col.append(item);
        });
      }
      grid.append(col);
    }
    $('compare-results').append(grid);
  } catch (error) {
    if (sequence === searchSequence) showNotice('Comparison failed', error.message);
  } finally {
    if (sequence === searchSequence) { $('compare-button').disabled = false; $('compare-button').textContent = 'Compare 3 modes'; }
  }
}
async function runEvalSuite() {
  const btn = $('run-eval');
  btn.disabled = true; btn.textContent = 'Running benchmark…';
  $('eval-status').textContent = 'Verifying gold targets and evaluating BM25, Embedding, and Hybrid…';
  $('eval-summary').replaceChildren(); $('eval-queries').replaceChildren();
  try {
    const split = $('eval-split').value;
    const report = await api('/api/eval', {split, k: 5});
    const v = report.verification;
    $('eval-status').textContent = `Verified (${v.verified_by}): ${v.total_queries} queries (${v.verified_targets} targets, ${v.verified_passages} exam passages) · ${report.elapsed_ms} ms`;
    const tableWrap = node('div', 'table-scroll');
    const table = node('table', 'eval-table');
    const thead = node('thead'), htr = node('tr');
    for (const h of ['Mode', 'Method', 'Hit@5', 'Recall@5', 'MRR', 'Passage Hit@5', 'Gap Acc.', 'False Gap', 'Avg ms']) htr.append(node('th', '', h));
    thead.append(htr); table.append(thead);
    const tbody = node('tbody');
    for (const mode of ['hybrid', 'bm25', 'embedding']) {
      const m = report.modes[mode]; if (!m) continue;
      const o = m.overall, tr = node('tr', mode === 'hybrid' ? 'highlight-row' : '');
      const pct = val => val === null || val === undefined ? '—' : (val * 100).toFixed(1) + '%';
      for (const cell of [
        mode.toUpperCase(),
        m.ranking_method,
        pct(o.hit_at_k),
        pct(o.recall_at_k),
        o.mrr.toFixed(3),
        pct(o.passage_hit_at_k),
        pct(o.gap_accuracy),
        pct(o.false_gap_rate),
        o.avg_elapsed_ms.toFixed(1)
      ]) tr.append(node('td', '', cell));
      tbody.append(tr);
    }
    table.append(tbody); tableWrap.append(table);
    $('eval-summary').append(tableWrap);

    const qWrap = node('div', 'table-scroll');
    const qTable = node('table', 'eval-table query-table');
    const qHead = node('thead'), qHtr = node('tr');
    for (const h of ['ID', 'Split', 'Type', 'Query (click to test live)', 'BM25', 'Embedding', 'Hybrid']) qHtr.append(node('th', '', h));
    qHead.append(qHtr); qTable.append(qHead);
    const qBody = node('tbody');
    for (const q of report.queries) {
      const tr = node('tr');
      tr.append(node('td', '', q.id), node('td', '', q.split), node('td', '', q.collection));
      const qTd = node('td');
      const qBtn = node('button', 'text-button', q.query_text);
      qBtn.addEventListener('click', () => {
        if (existingCorpus && ['all', 'curriculum', 'exam'].includes(q.collection)) $('collection-kind').value = q.collection;
        $('query').value = q.query_text;
        search();
      });
      qTd.append(qBtn); tr.append(qTd);
      for (const mode of ['bm25', 'embedding', 'hybrid']) {
        const mr = q.modes[mode];
        const ok = q.expected_status === 'gap' ? mr.gap_correct : mr.hit;
        const badgeText = q.expected_status === 'gap'
          ? (mr.gap_correct ? '✓ gap' : '✗')
          : (mr.hit ? `✓ RR=${mr.rr.toFixed(2)}${mr.top_label ? ' (' + mr.top_label + ')' : ''}` : '✗ miss');
        tr.append(node('td', ok ? 'pass-cell' : 'fail-cell', badgeText));
      }
      qBody.append(tr);
    }
    qTable.append(qBody); qWrap.append(qTable);
    $('eval-queries').append(qWrap);
  } catch (error) {
    $('eval-status').textContent = 'Benchmark failed: ' + error.message;
  } finally {
    btn.disabled = false; btn.textContent = 'Run benchmark suite';
  }
}
$('search-form').addEventListener('submit', search);
$('compare-button').addEventListener('click', compareModes);
$('run-eval').addEventListener('click', runEvalSuite);
$('retrieval-mode').addEventListener('change', () => search());
$('collection-kind').addEventListener('change', () => search());
for (const button of document.querySelectorAll('[data-query]')) button.addEventListener('click', () => { $('query').value = button.dataset.query; search(); });
for (const button of document.querySelectorAll('.close')) button.addEventListener('click', () => button.closest('dialog').close());
$('add').addEventListener('click', () => { $('import-error').textContent = ''; $('import-dialog').showModal(); });
$('import-file').addEventListener('change', async event => {
  const file = event.target.files[0]; if (!file) return;
  if (file.size > 500000) { $('import-error').textContent = 'Choose a text file smaller than 500 KB.'; return; }
  $('import-content').value = await file.text();
  if (!$('import-title').value) $('import-title').value = file.name.replace(/\.(txt|md)$/i, '');
});
$('import-form').addEventListener('submit', async event => {
  event.preventDefault(); const button = event.submitter; button.disabled = true;
  try {
    await api('/api/documents', {title: $('import-title').value, content: $('import-content').value, subject: $('import-subject').value,
      grade: Number($('import-grade').value), chapter: $('import-chapter').value ? Number($('import-chapter').value) : null,
      lesson: $('import-lesson').value ? Number($('import-lesson').value) : null, semester: $('import-semester').value ? Number($('import-semester').value) : null,
      source_locator: $('import-source').value, permission_confirmed: $('permission').checked});
    await loadCollection(); $('import-dialog').close(); $('import-form').reset();
    showNotice('Document added', 'Your text is available in the source collection. Run a query with its subject and scope to retrieve it.');
  } catch (error) { $('import-error').textContent = error.message; }
  finally { button.disabled = false; }
});
loadCollection().then(() => search()).catch(error => showNotice('Could not load collection', error.message));
