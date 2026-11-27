import { ApiError, resolveApiUrl } from './examService.ts';

export type DocumentKind = 'sample_exam' | 'matrix' | 'supplementary';
export interface InputDocument {
  schema_version: 'input-document-v1'; id: string; filename: string; kind: DocumentKind;
  size: number; sha256: string; characters: number; preview: string;
}
export interface DocumentPolicy {
  schema_version: string; max_files: number; max_bytes: number;
  max_characters: number; extensions: string[];
}
export const documentKinds: Record<DocumentKind, string> = {
  sample_exam: 'Đề mẫu', matrix: 'Ma trận', supplementary: 'Tài liệu thêm',
};
async function documentRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(resolveApiUrl(path), init); }
  catch { throw new ApiError('Không kết nối được máy chủ để tải tài liệu.', 'network_error'); }
  const body = await response.json();
  if (!response.ok) throw new ApiError(body.error?.message || 'Không tải được tài liệu.', body.error?.code, response.status);
  return body;
}
export const getDocumentPolicy = () => documentRequest<DocumentPolicy>('/api/input-documents/policy');
export function validateDocument(file: Pick<File, 'name' | 'size'>, count: number, policy: DocumentPolicy): string | undefined {
  if (count >= policy.max_files) return `Tối đa ${policy.max_files} tài liệu cho mỗi đề.`;
  if (!policy.extensions.some(ext => file.name.toLowerCase().endsWith(ext))) return 'Định dạng tệp chưa hỗ trợ.';
  if (!file.size) return 'Tài liệu rỗng.';
  if (file.size > policy.max_bytes) return `Tệp vượt quá ${policy.max_bytes / 1048576} MiB.`;
}
export const uploadDocument = (file: File, kind: DocumentKind) => documentRequest<InputDocument>(
  `/api/input-documents?${new URLSearchParams({ filename: file.name, kind })}`,
  { method: 'POST', headers: { 'Content-Type': 'application/octet-stream' }, body: file },
);
