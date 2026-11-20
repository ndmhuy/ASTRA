import React, { useMemo, useState } from 'react';
import { Check, FileText, FolderOpen, Pencil, Plus, Search, Trash2, X } from 'lucide-react';
import type { ExamSession } from '../state/examSessions';

interface ExamStorageViewProps {
  sessions: ExamSession[];
  activeId: string | null;
  onNew: () => void;
  onOpen: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

type StorageFilter = 'all' | 'approved' | 'pending' | 'generating' | 'draft' | 'error';

function formatCreatedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function resolveStatusInfo(session: ExamSession): { label: string; className: string; bucket: Exclude<StorageFilter, 'all'> } {
  if (session.status === 'generating') {
    return { label: 'Đang soạn', className: 'is-generating', bucket: 'generating' };
  }
  if (session.status === 'error') {
    return { label: 'Lỗi', className: 'is-error', bucket: 'error' };
  }
  if (session.status === 'complete') {
    if (session.package?.approved) {
      return { label: 'Đã phê duyệt', className: 'is-approved', bucket: 'approved' };
    }
    return { label: 'Chờ duyệt', className: 'is-pending', bucket: 'pending' };
  }
  return { label: 'Bản nháp', className: 'is-draft', bucket: 'draft' };
}

export const ExamStorageView: React.FC<ExamStorageViewProps> = ({
  sessions,
  activeId,
  onNew,
  onOpen,
  onRename,
  onDelete,
}) => {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<StorageFilter>('all');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const counts = useMemo(() => {
    const map: Record<StorageFilter, number> = {
      all: sessions.length,
      approved: 0,
      pending: 0,
      generating: 0,
      draft: 0,
      error: 0,
    };
    for (const session of sessions) {
      map[resolveStatusInfo(session).bucket] += 1;
    }
    return map;
  }, [sessions]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return sessions.filter(session => {
      const info = resolveStatusInfo(session);
      if (filter !== 'all' && info.bucket !== filter) return false;
      if (!q) return true;
      const haystack = `${session.title} ${session.meta?.subject || ''} ${session.id.slice(0, 8)}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [sessions, filter, query]);

  const startRename = (session: ExamSession) => {
    setEditingId(session.id);
    setDraftTitle(session.title);
    setDeleteId(null);
  };

  const commitRename = (id: string) => {
    if (draftTitle.trim()) {
      onRename(id, draftTitle);
    }
    setEditingId(null);
  };

  const filterItems: { id: StorageFilter; label: string }[] = [
    { id: 'all', label: 'Tất cả' },
    { id: 'approved', label: 'Đã duyệt' },
    { id: 'pending', label: 'Chờ duyệt' },
    { id: 'generating', label: 'Đang soạn' },
    { id: 'draft', label: 'Bản nháp' },
    { id: 'error', label: 'Lỗi' },
  ];

  return (
    <main className="exam-storage-view" aria-labelledby="storage-heading">
      <div className="storage-inner">
        <header className="storage-header">
          <div>
            <span className="storage-eyebrow">LƯU TRỮ ĐỀ THI</span>
            <div className="storage-title-row">
              <h1 id="storage-heading">Kho đề của tôi</h1>
              <span className="storage-total-badge">{sessions.length} đề</span>
            </div>
            <p className="storage-subtitle">
              Lưu cục bộ trên trình duyệt này và liên kết với phiên làm việc của máy chủ cục bộ (chưa đồng bộ đám mây).
            </p>
          </div>
          <button type="button" className="button-primary" onClick={onNew}>
            <Plus size={16} aria-hidden="true" />
            Tạo đề mới
          </button>
        </header>

        <div className="storage-toolbar">
          <label className="storage-search">
            <Search size={15} aria-hidden="true" />
            <input
              type="search"
              aria-label="Tìm đề trong kho"
              placeholder="Tìm theo tên đề hoặc môn học..."
              value={query}
              onChange={event => setQuery(event.target.value)}
            />
          </label>
          <div className="storage-filters" role="group" aria-label="Lọc theo trạng thái">
            {filterItems.map(item => (
              <button
                key={item.id}
                type="button"
                aria-pressed={filter === item.id}
                onClick={() => setFilter(item.id)}
              >
                {item.label} ({counts[item.id]})
              </button>
            ))}
          </div>
        </div>

        {sessions.length === 0 ? (
          <section className="storage-empty">
            <FolderOpen size={30} aria-hidden="true" />
            <h2>Kho đề chưa có đề thi nào</h2>
            <p>Bắt đầu tạo đề mới từ mẫu chuẩn hoặc trao đổi với ASTRA để lưu bài làm tại đây.</p>
            <button type="button" className="button-primary" onClick={onNew}>
              <Plus size={15} aria-hidden="true" />
              Bắt đầu tạo đề
            </button>
          </section>
        ) : filtered.length === 0 ? (
          <section className="storage-empty">
            <Search size={26} aria-hidden="true" />
            <h2>Không tìm thấy đề phù hợp</h2>
            <p>Thử đổi từ khóa tìm kiếm hoặc chuyển bộ lọc sang “Tất cả”.</p>
          </section>
        ) : (
          <ul className="storage-list">
            {filtered.map(session => {
              const statusInfo = resolveStatusInfo(session);
              const isEditing = editingId === session.id;
              const isDeleting = deleteId === session.id;
              const isCurrent = session.id === activeId;
              const metaSummary = session.meta
                ? `${session.meta.subject} · ${session.meta.totalCount} câu · ${session.meta.duration} phút`
                : session.mode === 'custom'
                  ? 'Soạn theo yêu cầu · Chưa tạo câu hỏi'
                  : 'Từ mẫu chuẩn · Chưa tạo câu hỏi';

              return (
                <li key={session.id} className={`storage-row ${isCurrent ? 'is-current' : ''}`}>
                  <div className="storage-row-main">
                    <div className="storage-row-icon" aria-hidden="true">
                      <FileText size={17} />
                    </div>
                    <div className="storage-row-body">
                      {isEditing ? (
                        <div className="storage-rename-row">
                          <input
                            type="text"
                            maxLength={100}
                            aria-label="Tên đề mới"
                            value={draftTitle}
                            onChange={event => setDraftTitle(event.target.value)}
                            onKeyDown={event => {
                              if (event.key === 'Enter') commitRename(session.id);
                              if (event.key === 'Escape') setEditingId(null);
                            }}
                            autoFocus
                          />
                          <button type="button" className="button-primary" onClick={() => commitRename(session.id)}>
                            <Check size={14} aria-hidden="true" />
                            Lưu
                          </button>
                          <button type="button" className="button-secondary" onClick={() => setEditingId(null)}>
                            <X size={14} aria-hidden="true" />
                            Hủy
                          </button>
                        </div>
                      ) : (
                        <>
                          <div className="storage-row-heading">
                            <button type="button" className="storage-row-title" onClick={() => onOpen(session.id)}>
                              {session.title}
                            </button>
                            <span className={`storage-badge ${statusInfo.className}`}>{statusInfo.label}</span>
                          </div>
                          <div className="storage-row-meta">
                            <span>{metaSummary}</span>
                            <span>·</span>
                            <span>Mã #{session.id.slice(0, 6)}</span>
                            <span>·</span>
                            <time dateTime={session.createdAt}>{formatCreatedAt(session.createdAt)}</time>
                          </div>
                        </>
                      )}
                    </div>
                    {!isEditing && (
                      <div className="storage-actions">
                        <button type="button" className="button-secondary" onClick={() => onOpen(session.id)}>
                          Mở đề
                        </button>
                        <button
                          type="button"
                          className="storage-icon-btn"
                          title={`Đổi tên ${session.title}`}
                          aria-label={`Đổi tên ${session.title}`}
                          onClick={() => startRename(session)}
                        >
                          <Pencil size={14} aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          className="storage-icon-btn is-danger"
                          title={`Xóa ${session.title}`}
                          aria-label={`Xóa ${session.title}`}
                          onClick={() => setDeleteId(isDeleting ? null : session.id)}
                        >
                          <Trash2 size={14} aria-hidden="true" />
                        </button>
                      </div>
                    )}
                  </div>

                  {isDeleting && (
                    <div className="storage-delete-bar" role="alert">
                      <span>
                        {session.status === 'generating'
                          ? 'Xóa khỏi danh sách hiển thị? Lưu ý: tiến trình tạo đề đang chạy trên máy chủ sẽ không bị hủy.'
                          : 'Xóa đề này khỏi Kho đề trên trình duyệt?'}
                      </span>
                      <div className="storage-delete-btns">
                        <button
                          type="button"
                          className="storage-delete-confirm"
                          onClick={() => {
                            onDelete(session.id);
                            setDeleteId(null);
                          }}
                        >
                          Xác nhận xóa
                        </button>
                        <button type="button" className="button-secondary" onClick={() => setDeleteId(null)}>
                          Hủy
                        </button>
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </main>
  );
};
