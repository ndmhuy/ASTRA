import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatCapabilitySuccess, formatUserError, formatVisualWarning } from '../src/utils/userMessages.ts';
import { actionFailureMessage } from '../src/agent/executor.ts';

test('formatUserError converts technical codes and English errors into friendly Vietnamese', () => {
  assert.match(formatUserError('Server error', 'provider_http_error'), /trục trặc tạm thời/);
  assert.match(formatUserError(new Error('HTTP 503 Service Unavailable')), /trục trặc tạm thời/);
  assert.match(formatUserError('Invalid API key', 'auth_error'), /Cấu hình dịch vụ AI/);
  assert.match(formatUserError('Budget exceeded', 'spend_limit_exceeded'), /hạn mức sử dụng/);
  assert.match(formatUserError('latex missing', 'latex_compiler_unavailable'), /Chưa bật tính năng tạo bản in PDF/);
  assert.match(formatUserError('compile failed', 'latex_compile_failed'), /Chưa thể tạo bản xem trước PDF/);
  assert.match(formatUserError('Failed to fetch', 'network_error'), /Không thể kết nối đến hệ thống/);
  assert.match(formatUserError('{"detail":"raw trace"}'), /Hệ thống gặp trục trặc/);
  assert.equal(formatUserError('Chưa chọn đúng đề mẫu hợp lệ.'), 'Chưa chọn đúng đề mẫu hợp lệ.');
});

test('formatCapabilitySuccess and actionFailureMessage avoid leaking raw capability IDs or codes', () => {
  const openMsg = formatCapabilitySuccess('ui.exam.open_setup');
  assert.equal(openMsg, 'Đã mở hộp thiết lập đề thi.');
  assert.equal(openMsg.includes('ui.exam'), false);

  const failMsg = actionFailureMessage('EXAM_NOT_READY');
  assert.equal(failMsg.includes('EXAM_NOT_READY'), false);
  assert.match(failMsg, /Chưa có đề thi sẵn sàng/);
});

test('formatVisualWarning removes raw warning codes', () => {
  const msg = formatVisualWarning({ questionId: 'P1-8', code: 'missing_figure_code' });
  assert.equal(msg.includes('missing_figure_code'), false);
  assert.match(msg, /Câu P1-8/);
});
