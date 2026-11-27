import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateDocument, uploadDocument } from '../src/services/inputDocuments.ts';
import { ExamSessions } from '../src/state/examSessions.ts';

const policy = { max_files: 5, max_bytes: 10485760, extensions: ['.pdf', '.docx', '.txt'] };
test('upload validation checks file count, size, empty files and case-insensitive extensions', () => {
  assert.equal(validateDocument({ name: 'Mẫu.PDF', size: 50 }, 4, policy), undefined);
  assert.match(validateDocument({ name: 'x.pdf', size: 1 }, 5, policy), /5/);
  assert.match(validateDocument({ name: 'x.exe', size: 1 }, 0, policy), /chưa hỗ trợ/);
  assert.match(validateDocument({ name: 'x.txt', size: 0 }, 0, policy), /rỗng/);
  assert.match(validateDocument({ name: 'x.txt', size: policy.max_bytes + 1 }, 0, policy), /MiB/);
});
test('upload sends actual file bytes with its selected role and exposes server errors', async t => {
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
