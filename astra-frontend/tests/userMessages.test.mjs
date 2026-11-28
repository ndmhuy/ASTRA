import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  formatProgressStatus,
  formatVisualWarning,
  humanizeErrorMessage,
} from '../src/utils/userMessages.ts';

test('humanizeErrorMessage translates technical errors to natural Vietnamese', () => {
  assert.match(humanizeErrorMessage('Configure a real EXAM_PROVIDER and model', 'provider_not_configured'), /dịch vụ AI/);
  assert.match(humanizeErrorMessage('Bad Gateway', 'request_failed'), /máy chủ/);
  assert.match(humanizeErrorMessage('Model provider failed (HTTP 503)', 'provider_unavailable'), /Dịch vụ AI/);
  assert.equal(humanizeErrorMessage('Provider overloaded', 'provider_unavailable'), 'Provider overloaded');
  // Previously saved connection errors used the misleading generic busy text.
  assert.match(humanizeErrorMessage('Dịch vụ AI đang bận', 'provider_connection_failed'), /API Base URL/);
  assert.match(humanizeErrorMessage('API key chưa có quyền dùng model này.', 'provider_access_denied'), /HTTP 403.*endpoint và cách xác thực/);
});

test('formatProgressStatus converts legacy raw progress labels to Vietnamese', () => {
  const formatted = formatProgressStatus('composer / LOGIC_91_102 / revision 1');
  assert.equal(formatted, 'Đang soạn câu hỏi · Logic & phân tích số liệu');
  assert.ok(!/composer|LOGIC_|revision/i.test(formatted));
  assert.equal(formatProgressStatus('solver / P2 / revision 2'), 'Đang giải kiểm tra đáp án · Phần II (Đúng/Sai) (lượt rà soát lại)');
});

test('formatVisualWarning hides internal warning codes', () => {
  assert.match(formatVisualWarning('missing_illustration_request: referenced figure'), /hình minh họa/);
  assert.match(formatVisualWarning('pseudo_table: replace pipe'), /Bảng số liệu/);
});
