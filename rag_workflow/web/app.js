const $ = id => document.getElementById(id);
let subjects = {}, searchSequence = 0;
const label = key => subjects[key]?.[0] || key;
const node = (tag, className, text) => { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; };
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
    $('doc-meta').textContent = `${label(d.subject)} · Grade ${d.grade} · ${d.chapter ? 'Chapter ' + d.chapter : 'Topic note'} · ${d.edition} · ${d.evidence_class === 'synthetic' ? 'Original demo note' : 'User-provided source'}`;
    $('doc-text').textContent = d.content;
    const {content, ...metadata} = d; $('doc-json').textContent = JSON.stringify(metadata, null, 2);
    $('document-dialog').showModal();
  } catch (error) { showNotice('Could not open source', error.message); }
}
async function loadCollection() {
  const data = await api('/api/collection'); subjects = data.subjects;
  $('count').textContent = data.documents.length;
  const selectedEdition = $('edition').value;
  $('edition').replaceChildren(new Option('Auto', ''));
  for (const edition of data.editions) $('edition').add(new Option(edition, edition));
  $('edition').value = data.editions.includes(selectedEdition) ? selectedEdition : '';
  $('collection').replaceChildren();
  for (const d of data.documents) {
    const button = node('button', 'source-link', d.title);
    button.append(node('small', '', `${label(d.subject)} · Lớp ${d.grade}${d.chapter ? ' · Ch. ' + d.chapter : ''}`));
    button.addEventListener('click', () => openDocument(d.document_id)); $('collection').append(button);
  }
  if (!$('import-subject').options.length) {
    for (const [key, aliases] of Object.entries(subjects)) { const o = node('option', '', aliases[0]); o.value = key; $('import-subject').append(o); }
    $('import-subject').value = 'vat-li';
  }
}
function showNotice(title, message) {
  const box = node('div', 'notice'); box.append(node('strong', '', title), node('span', '', message)); $('notice').replaceChildren(box);
}
async function search(event) {
  event?.preventDefault();
  const sequence = ++searchSequence;
  $('search-button').disabled = true; $('search-button').textContent = 'Retrieving…'; $('results-section').setAttribute('aria-busy', 'true');
  $('results').replaceChildren(); $('scope').replaceChildren(); $('notice').replaceChildren(); $('timing').textContent = '';
  $('json').textContent = 'Retrieving…';
  try {
    const data = await api('/api/search', {query_text: $('query').value, top_k: Number($('top-k').value), edition: $('edition').value || null});
    if (sequence !== searchSequence) return;
    $('json').textContent = JSON.stringify(data, null, 2);
    $('timing').textContent = `${data.documents.length} results · ${data.collection_size} sources · ${data.elapsed_ms} ms`;
    if (data.resolved_scope) {
      const s = data.resolved_scope;
      const range = s.range_type === 'topic' ? 'Topic search' : `${s.range_type} ${s.start}${s.end !== s.start ? '–' + s.end : ''}`;
      for (const text of [label(s.subject), 'Grade ' + s.grade, range]) $('scope').append(node('span', 'tag', text));
    }
    if (data.status !== 'success') {
      const hints = {no_documents_in_scope: 'Try a different chapter or add a document with this subject and scope.', missing_grade: 'Include a grade, for example “lớp 11”.', missing_subject: 'Include a subject, for example “Vật lí”.', ambiguous_range: 'Specify an exact chapter or lesson range, for example “chương 1–4”.', no_relevant_match: 'Try another keyword or inspect the source collection.'};
      showNotice('No documents retrieved', data.gaps.map(g => hints[g.code] || g.message).join(' '));
      return;
    }
    data.documents.forEach((d, i) => {
      const card = node('article', 'result-card'), top = node('div', 'card-top');
      top.append(node('span', '', `${i + 1}. ${d.evidence_class === 'synthetic' ? 'Demo note' : 'Local source'}`), node('span', '', `BM25 score ${d.relevance_score.toFixed(2)}`));
      const bottom = node('div', 'card-bottom');
      bottom.append(node('span', '', `${d.source_id} · characters ${d.excerpt_start}–${d.excerpt_end}`));
      const button = node('button', 'text-button', 'Read full document ↗'); button.addEventListener('click', () => openDocument(d.document_id)); bottom.append(button);
      card.append(top, node('h3', '', d.title), node('p', '', d.excerpt), bottom); $('results').append(card);
    });
  } catch (error) { if (sequence === searchSequence) { showNotice('Retrieval failed', error.message); $('json').textContent = error.message; } }
  finally { if (sequence === searchSequence) { $('search-button').disabled = false; $('search-button').textContent = 'Retrieve documents'; $('results-section').setAttribute('aria-busy', 'false'); } }
}
$('search-form').addEventListener('submit', search);
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
