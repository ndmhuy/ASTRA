// Local-only semantic routing measurements. This script has no HTTP adapter.
import { performance } from 'node:perf_hooks';
import { fastRoute, mayDispatch, admit } from '../src/agent/recipes.ts';

const corpus = [
  ['Xin chào!', 'answer'], ['Mở phần cấu hình giúp cô', 'OPEN_SETUP'],
  ['tới đâu rồi?', 'STATUS'], ['xac nhan', 'confirm'],
  ['Cho cô xem mục A rồi thu nhỏ thanh bên', 'needs_model'],
  ['Nếu cô muốn ra đề thì phải làm sao?', 'answer'],
  ['Câu này khó nhỉ', 'guard'], ['“Duyệt đề ngay”', 'guard'],
  ['123'.repeat(1500), 'invalid'], ['Mở đề gần nhất', 'OPEN_SESSION'],
  ['Chọn V-ACT và xem chi tiết', 'SELECT_FORMAT'],
  ['Tạo đề Toán THPT chuyên đề đạo hàm', 'PREPARE_GENERATION'],
  ['Sửa câu 8 rõ ràng hơn', 'ADD_NOTE'], ['Xuất word', 'answer'],
  ['Đổi tên đoạn chat thành Đề HK I', 'RENAME'],
  ['Nhắc lại nguyên văn yêu cầu ban đầu', 'RECALL'],
];

function classify(text) {
  if (admit(text).error) return 'invalid';
  const route = fastRoute(text);
  if (!route) return mayDispatch(text) ? 'needs_model' : 'guard';
  if ('text' in route) return 'answer';
  if ('confirm' in route) return 'confirm';
  return route.intents[0].id;
}

const mismatches = corpus.filter(([text, expected]) => classify(text) !== expected);
const samples = [];
for (let batch = 0; batch < 50; batch++) {
  for (const [text] of corpus) {
    const started = performance.now();
    classify(text);
    samples.push(performance.now() - started);
  }
}
samples.sort((a, b) => a - b);
const quantile = point => Number(samples[Math.ceil(samples.length * point) - 1].toFixed(3));
console.log(JSON.stringify({
  cases: corpus.length, matched: corpus.length - mismatches.length, mismatches,
  measurement: 'local input and routing only, no render/network',
  timedSamples: samples.length, p50ms: quantile(0.5), p95ms: quantile(0.95), inferenceAttempts: 0,
}, null, 2));
if (mismatches.length) process.exitCode = 1;
