import React, { useState } from 'react';
import type { ExamSession } from '../state/examSessions';
import { ArrowRight, FileText, SlidersHorizontal, Search, Library, Clock3, CheckCheck, FolderOpen } from 'lucide-react';

interface OnboardingForkProps {
  onQuickMode: () => void;
  onProMode: () => void;
  sessions: ExamSession[];
  onOpenSession: (id: string) => void;
}

export const OnboardingFork: React.FC<OnboardingForkProps> = ({ onQuickMode, onProMode, sessions, onOpenSession }) => {
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');
  const complete = sessions.filter(s => s.status === 'complete').length;
  const tabs = [{ id: 'all', label: 'Tất cả đề thi', icon: Library, count: sessions.length }, { id: 'draft', label: 'Đang soạn', icon: Clock3, count: sessions.length - complete }, { id: 'complete', label: 'Đã hoàn thành', icon: CheckCheck, count: complete }];
  const visible = sessions.filter(s => (filter === 'all' || (filter === 'complete' ? s.status === 'complete' : s.status !== 'complete')) && `${s.title} ${s.meta?.subject || ''}`.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')));
  return <div className="library-layout">
    <main className="home-screen"><div className="home-content">
      <header className="page-heading"><div><h1>Soạn đề thi</h1><p>Chọn cách tạo đề. Bạn có thể xem và sửa câu hỏi trước khi tải về.</p></div></header>
      <section className="creation-panel" aria-labelledby="create-heading">
        <div className="creation-intro"><h2 id="create-heading">Bạn muốn tạo đề như thế nào?</h2></div>
        <div className="creation-options"><button className="creation-option" onClick={onQuickMode}><span className="creation-icon"><FileText size={21} strokeWidth={1.5} /></span><span><strong>Tạo đề từ mẫu có sẵn</strong><small>Chọn môn học và loại đề để bắt đầu nhanh.</small></span><ArrowRight size={18} /></button><button className="creation-option" onClick={onProMode}><span className="creation-icon"><SlidersHorizontal size={21} strokeWidth={1.5} /></span><span><strong>Tự mô tả đề muốn tạo</strong><small>Nhập chủ đề, số câu và độ khó bạn cần.</small></span><ArrowRight size={18} /></button></div>
      </section>
      <section className="exam-library" aria-labelledby="library-heading"><header className="library-heading"><div><h2 id="library-heading">Đề thi của bạn</h2><span>{visible.length} đề thi</span></div>{sessions.length > 0 && <label className="library-search"><Search size={17} /><input aria-label="Tìm đề thi" placeholder="Tìm tên đề, môn học…" value={query} onChange={e => setQuery(e.target.value)} /></label>}</header>
        {sessions.length > 0 && <nav className="library-filters" aria-label="Lọc đề thi">{tabs.map(({ id, label, count }) => <button key={id} aria-pressed={filter === id} onClick={() => setFilter(id)}>{label} <span>{count}</span></button>)}</nav>}
        <div className="library-table">{visible.length > 0 && <div className="table-labels" aria-hidden="true"><span>TÊN ĐỀ THI</span><span>TRẠNG THÁI</span><span>THỜI GIAN TẠO</span><span /></div>}
          {visible.length ? <ul className="exam-rows">{visible.map(session => {
            const flagged = session.questions.filter(q => q.status === 'FLAGGED').length;
            return <li key={session.id}><button className="exam-row" onClick={() => onOpenSession(session.id)}><span className="exam-row-title"><span className="document-icon"><FileText size={21} strokeWidth={1.5} /></span><span><strong>{session.title}</strong><small>{session.meta ? `${session.meta.subject} · ${session.meta.totalCount} câu · ${session.meta.duration} phút` : 'Chưa thiết lập môn học'} · {session.mode === 'template' ? 'Từ mẫu' : 'Theo yêu cầu'}</small></span></span><span className={`status-tag status-${session.status}`}>{session.status === 'generating' ? `Đang soạn · ${session.meta?.completedCount || 0}/${session.meta?.totalCount || 0}` : session.status === 'complete' ? flagged ? `${flagged} câu cần xem lại` : 'Đã hoàn thành' : session.status === 'error' ? 'Cần thử lại' : 'Bản nháp'}</span><time dateTime={new Date(session.createdAt).toISOString()}>{new Date(session.createdAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</time><ArrowRight size={17} /></button></li>;
          })}</ul> : <div className="library-empty"><span className="empty-folder"><FolderOpen size={30} strokeWidth={1.2} /></span><h3>{query ? 'Không tìm thấy đề thi' : filter === 'complete' ? 'Chưa có đề hoàn thành' : filter === 'draft' && sessions.length ? 'Không có đề đang soạn' : 'Bạn chưa có đề thi nào'}</h3><p>{query ? 'Thử tìm bằng tên đề hoặc môn học khác.' : filter === 'complete' ? 'Đề đã soạn xong sẽ được lưu tại đây trong phiên này.' : 'Các đề thi sẽ xuất hiện ở đây. Chọn một cách tạo đề ở phía trên để bắt đầu.'}</p></div>}
        </div><p className="session-storage-note"><Clock3 size={13} /> Lưu ý: Hãy tải đề về trước khi đóng hoặc tải lại trang để tránh mất nội dung.</p>
      </section>
    </div></main>
  </div>;
};
