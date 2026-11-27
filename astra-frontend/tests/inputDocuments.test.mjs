import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateDocument, uploadDocument, getActiveUploads } from '../src/services/inputDocuments.ts';
import { fastRoute } from '../src/agent/recipes.ts';
import { ExamSessions } from '../src/state/examSessions.ts';

const policy = { max_files: 5, max_bytes: 10485760, extensions: ['.pdf', '.docx', '.txt'] };
test('upload validation checks file count, filename length, size, empty files and case-insensitive extensions', () => {
  assert.equal(validateDocument({ name: 'Mẫu.PDF', size: 50 }, 4, policy), undefined);
  assert.match(validateDocument({ name: 'x.pdf', size: 1 }, 5, policy), /5/);
  assert.match(validateDocument({ name: `${'a'.repeat(180)}.txt`, size: 10 }, 0, policy), /180/);
  assert.match(validateDocument({ name: 'x.exe', size: 1 }, 0, policy), /chưa hỗ trợ/);
  assert.match(validateDocument({ name: 'x.txt', size: 0 }, 0, policy), /rỗng/);
  assert.match(validateDocument({ name: 'x.txt', size: policy.max_bytes + 1 }, 0, policy), /MiB/);
});
test('upload sends actual file bytes with its selected role, exposes server errors, and handles non-JSON/abort', async t => {
  const original = globalThis.fetch;
  t.after(() => { globalThis.fetch = original; });
  const file = new File(['Ma trận tổng hợp'], 'ma trận.txt');
  globalThis.fetch = async (url, init) => {
    assert.equal(new URL(url, 'http://localhost').searchParams.get('kind'), 'matrix');
    assert.equal(new URL(url, 'http://localhost').searchParams.get('filename'), file.name);
    assert.equal(await init.body.text(), 'Ma trận tổng hợp');
    return Response.json({ id: 'document' }, { status: 201 });
  };
  assert.deepEqual(await uploadDocument(file, 'matrix'), { id: 'document' });
  globalThis.fetch = async () => Response.json({ error: { code: 'no_document_text', message: 'PDF cần OCR' } }, { status: 422 });
  await assert.rejects(uploadDocument(file, 'matrix'), error => error.code === 'no_document_text' && error.message === 'PDF cần OCR');
  globalThis.fetch = async () => new Response('Bad Gateway', { status: 502 });
  await assert.rejects(uploadDocument(file, 'matrix'), error => error.code === 'request_failed' && error.status === 502 && !/Unexpected token/.test(error.message));
  const controller = new AbortController();
  controller.abort();
  globalThis.fetch = async (_url, init) => { throw init.signal.reason ?? new DOMException('Aborted', 'AbortError'); };
  await assert.rejects(uploadDocument(file, 'matrix', controller.signal), error => error.name === 'AbortError');
});
test('attachment-only send and upload query route cleanly without requiring AI chat', () => {
  assert.deepEqual(fastRoute('Soạn đề dựa trên tài liệu đính kèm.'), { intents: [{ id: 'OPEN_SETUP', args: {} }] });
  assert.match(fastRoute('upload').text, /Đính kèm tài liệu/);
});
test('workspace attachments persist on the server and reload into their own workspace', async () => {
  const workspaces = new Map();
  const service = { workspaceLibrary: {
    async save(id, draft, revision) { workspaces.set(id, { ...draft, id, revision: revision + 1, createdAt: new Date().toISOString(), jobId: null, jobStatus: null, jobMeta: null, jobError: null }); return { revision: revision + 1 }; },
    async list() { return { workspaces: [...workspaces.values()] }; },
  } };
  const store = new ExamSessions(service);
  const first = store.create('custom');
  const second = store.create('custom');
  const document = { id: crypto.randomUUID(), filename: 'matrix.csv', kind: 'matrix', preview: 'Synthetic matrix' };
  store.setInputDocuments(first, [document]);
  await store.retryLibrary();
  const reader = new ExamSessions(service);
  await reader.loadLibrary();
  assert.deepEqual(reader.getSnapshot().find(item => item.id === first).inputDocuments, [document]);
  assert.deepEqual(reader.getSnapshot().find(item => item.id === second).inputDocuments ?? [], []);
  store.setInputDocuments(first, []);
  await store.retryLibrary();
  await reader.loadLibrary();
  assert.deepEqual(reader.getSnapshot().find(item => item.id === first).inputDocuments, []);
  store.dispose(); reader.dispose();
});

test('generation stays blocked until every concurrent upload settles', async t => {
  const original = globalThis.fetch;
  t.after(() => { globalThis.fetch = original; });
  const pending = [];
  globalThis.fetch = () => new Promise(resolve => pending.push(resolve));
  const file = new File(['reference'], 'reference.txt');
  const first = uploadDocument(file, 'sample_exam');
  const second = uploadDocument(file, 'matrix');
  assert.equal(getActiveUploads(), 2);
  pending[1](Response.json({ id: 'second' }, { status: 201 }));
  await second;
  assert.equal(getActiveUploads(), 1);
  pending[0](Response.json({ id: 'first' }, { status: 201 }));
  await first;
  assert.equal(getActiveUploads(), 0);
});
