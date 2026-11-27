import { ApiError, resolveApiUrl } from './examService.ts';

export type DocumentKind = 'sample_exam' | 'matrix' | 'supplementary';
export interface InputDocument {
  schema_version: 'input-document-v1'; id: string; filename: string; kind: DocumentKind;
  size: number; sha256: string; characters: number; preview: string;
}
export type InputDocumentsUpdate = InputDocument[] | ((documents: InputDocument[]) => InputDocument[]);

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
  catch (error) {
    if (init?.signal?.aborted || (error instanceof DOMException && error.name === 'AbortError')) throw error;
    throw new ApiError('Không kết nối được máy chủ để tải tài liệu.', 'network_error');
  }
  let body: { error?: { message?: string; code?: string } } | null = null;
  try { body = await response.json(); }
  catch {
    if (!response.ok) throw new ApiError('Không tải được tài liệu. Máy chủ phản hồi không hợp lệ.', 'request_failed', response.status);
    throw new ApiError('Phản hồi từ máy chủ không đúng định dạng.', 'invalid_response', response.status);
  }
  if (!response.ok) throw new ApiError(body?.error?.message || 'Không tải được tài liệu.', body?.error?.code, response.status);
  return body as T;
}
export const getDocumentPolicy = () => documentRequest<DocumentPolicy>('/api/input-documents/policy');
export function validateDocument(file: Pick<File, 'name' | 'size'>, count: number, policy: DocumentPolicy): string | undefined {
  if (count >= policy.max_files) return `Tối đa ${policy.max_files} tài liệu cho mỗi đề.`;
  const trimmedName = file.name.trim();
  if (!trimmedName || trimmedName.length > 180) return 'Tên tài liệu không hợp lệ (tối đa 180 ký tự).';
  if (!policy.extensions.some(ext => trimmedName.toLowerCase().endsWith(ext))) return 'Định dạng tệp chưa hỗ trợ.';
  if (!file.size) return 'Tài liệu rỗng.';
  if (file.size > policy.max_bytes) return `Tệp vượt quá ${policy.max_bytes / 1048576} MiB.`;
}
let activeUploads = 0;
const uploadListeners = new Set<() => void>();
export const getActiveUploads = () => activeUploads;
export const subscribeUploads = (listener: () => void) => {
  uploadListeners.add(listener);
  return () => { uploadListeners.delete(listener); };
};
function uploadActivity(delta: number) {
  activeUploads += delta;
  uploadListeners.forEach(listener => listener());
}
export async function uploadDocument(file: File, kind: DocumentKind, signal?: AbortSignal) {
  uploadActivity(1);
  try {
    return await documentRequest<InputDocument>(
      `/api/input-documents?${new URLSearchParams({ filename: file.name, kind })}`,
      { method: 'POST', headers: { 'Content-Type': 'application/octet-stream' }, body: file, signal },
    );
  } finally { uploadActivity(-1); }
}
