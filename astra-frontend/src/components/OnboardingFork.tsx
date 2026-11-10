import { StationeryArt } from './StationeryArt';
import { SchoolArt } from './SchoolArt';
import React, { useState } from 'react';
import type { ExamSession } from '../state/examSessions';
import { ArrowRight, FileText, Search, Trash2, Library, Clock3, CheckCheck, BookOpenCheck, Sparkles } from 'lucide-react';

interface OnboardingForkProps {
  tab: 'welcome' | 'create' | 'library';
  onTabChange: (tab: 'welcome' | 'create' | 'library') => void;
  onQuickMode: () => void;
  onProMode: () => void;
  sessions: ExamSession[];
  onDeleteSession: (id: string) => void;
  onOpenSession: (id: string) => void;
}

export const OnboardingFork: React.FC<OnboardingForkProps> = ({ tab, onTabChange, onQuickMode, onProMode, sessions, onOpenSession, onDeleteSession }) => {
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');
  const complete = sessions.filter(s => s.status === 'complete').length;
  const tabs = [{ id: 'all', label: 'Tất cả đề thi', icon: Library, count: sessions.length }, { id: 'draft', label: 'Đang soạn', icon: Clock3, count: sessions.length - complete }, { id: 'complete', label: 'Đã hoàn thành', icon: CheckCheck, count: complete }];
  const visible = sessions.filter(s => (filter === 'all' || (filter === 'complete' ? s.status === 'complete' : s.status !== 'complete')) && `${s.title} ${s.meta?.subject || ''}`.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')));
  return <div className="library-layout">
    <main className={`home-screen tab-${tab}`}><div className="home-content" key={tab}>
      {tab === 'welcome' && <header className="classroom-hero">
        <div className="hero-copy"><span className="hero-kicker">GÓC SOẠN ĐỀ CỦA THẦY CÔ</span><h1>Ý tưởng của thầy cô.<br />Khởi đầu của một<br /><em>đề thi hay.</em></h1><p>Từ ý tưởng đến trang đề hoàn chỉnh.<br />Cùng ASTRA dành thêm thời gian cho việc dạy học.</p><button className="hero-link" onClick={() => onTabChange('create')}>Bắt đầu soạn đề <ArrowRight size={20} /></button></div>
        <div className="hero-art"><StationeryArt kind="ruler" className="hero-ruler" /><span className="art-caption">Một chút cảm hứng cho lớp học</span><SchoolArt kind="globe" className="hero-globe" /><SchoolArt kind="book" className="hero-book" /><SchoolArt kind="bag" className="hero-bag" /><span className="art-star star-one">✦</span><span className="art-star star-two">✦</span><span className="art-note">Thầy cô lên ý tưởng,<br />ASTRA cùng soạn đề.</span></div>
      </header>}
      {tab === 'create' && <section className="creation-panel" aria-labelledby="create-heading">
        <div className="create-intro">
          <span className="create-eyebrow">SOẠN ĐỀ · ASTRA</span>
          <h1 id="create-heading">Một ý tưởng hay<br /><em>thành đề thi rõ ràng.</em></h1>
          <p>Chọn cách bắt đầu. Thầy cô luôn xem lại đề trước khi sử dụng.</p>
        </div>
        <div className="create-start-options">
          <button className="create-start-card create-start-quick" onClick={onQuickMode}>
            <span className="create-card-icon"><BookOpenCheck size={24} strokeWidth={1.7} /></span>
            <span className="create-card-copy"><strong>Tạo nhanh</strong><small>Chọn môn học và dạng đề có sẵn để bắt đầu trong vài bước.</small></span>
            <span className="create-card-action">Chọn mẫu <ArrowRight size={18} aria-hidden="true" /></span>
          </button>
          <button className="create-start-card create-start-custom" onClick={onProMode}>
            <span className="create-card-icon"><Sparkles size={24} strokeWidth={1.7} /></span>
            <span className="create-card-copy"><strong>Tùy chỉnh đề</strong><small>Mô tả chủ đề, số câu và độ khó trong không gian làm việc.</small></span>
            <span className="create-card-action">Bắt đầu viết <ArrowRight size={18} aria-hidden="true" /></span>
          </button>
        </div>
        {sessions.some(session => session.status === 'draft' || session.status === 'generating' || session.status === 'error') && <section className="create-recent" aria-label="Đề đang làm">
          <span className="create-eyebrow">TIẾP TỤC CÔNG VIỆC</span>
          <div>{sessions.filter(session => session.status === 'draft' || session.status === 'generating' || session.status === 'error').slice(0, 3).map(session => <button key={session.id} onClick={() => onOpenSession(session.id)}><span><strong>{session.title}</strong><small>{session.meta ? `${session.meta.subject} · ${session.meta.completedCount}/${session.meta.totalCount} câu` : 'Bản nháp'}</small></span><ArrowRight size={18} aria-hidden="true" /></button>)}</div>
        </section>}
      </section>}
      {tab === 'library' && <section className="exam-library" aria-labelledby="library-heading"><header className="library-heading"><div><StationeryArt kind="clipboard" className="library-clipboard" /><h2 id="library-heading">Tủ đề của thầy cô</h2><span>{visible.length} đề thi</span></div>{sessions.length > 0 && <label className="library-search"><Search size={17} /><input aria-label="Tìm đề thi" placeholder="Tìm tên đề, môn học…" value={query} onChange={e => setQuery(e.target.value)} /></label>}</header>
        {sessions.length > 0 && <nav className="library-filters" aria-label="Lọc đề thi">{tabs.map(({ id, label, count }) => <button key={id} aria-pressed={filter === id} onClick={() => setFilter(id)}>{label} <span>{count}</span></button>)}</nav>}
        <div className="library-table">{visible.length > 0 && <div className="table-labels" aria-hidden="true"><span>TÊN ĐỀ THI</span><span>TRẠNG THÁI</span><span>THỜI GIAN TẠO</span><span /></div>}
          {visible.length ? <ul className="exam-rows">{visible.map(session => {
            const flagged = session.questions.filter(q => q.status === 'FLAGGED').length;
            return <li key={session.id}><button className="exam-row" onClick={() => onOpenSession(session.id)}><span className="exam-row-title"><span className="document-icon"><FileText size={21} strokeWidth={1.5} /></span><span><strong>{session.title}</strong><small>{session.meta ? `${session.meta.subject} · ${session.meta.totalCount} câu · ${session.meta.duration} phút` : 'Chưa thiết lập môn học'} · {session.mode === 'template' ? 'Từ mẫu' : 'Theo yêu cầu'}</small></span></span><span className={`status-tag status-${session.status}`}>{session.status === 'generating' ? `Đang soạn · ${session.meta?.completedCount || 0}/${session.meta?.totalCount || 0}` : session.status === 'complete' ? flagged ? `${flagged} câu cần xem lại` : 'Đã hoàn thành' : session.status === 'error' ? 'Cần thử lại' : 'Bản nháp'}</span><time dateTime={new Date(session.createdAt).toISOString()}>{new Date(session.createdAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</time><ArrowRight size={17} /></button><div className="exam-delete-actions">{deleteId === session.id ? <><span>Xóa đề này?</span><button className="delete-confirm" onClick={() => { onDeleteSession(session.id); setDeleteId(null); }}>Xóa</button><button onClick={() => setDeleteId(null)}>Hủy</button></> : <button className="delete-trigger" aria-label={`Xóa ${session.title}`} onClick={() => setDeleteId(session.id)}><Trash2 size={16} aria-hidden="true" /> Xóa</button>}</div></li>;
          })}</ul> : <div className="library-empty"><SchoolArt kind="bag" className="empty-bag" /><h3>{query ? 'Không tìm thấy đề thi' : filter === 'complete' ? 'Chưa có đề hoàn thành' : filter === 'draft' && sessions.length ? 'Không có đề đang soạn' : 'Bạn chưa có đề thi nào'}</h3><p>{query ? 'Thử tìm bằng tên đề hoặc môn học khác.' : filter === 'complete' ? 'Đề đã soạn xong sẽ được lưu tại đây trong phiên này.' : 'Các đề thi sẽ xuất hiện ở đây. Mở mục Soạn đề để bắt đầu.'}</p></div>}
        </div><p className="session-storage-note"><Clock3 size={13} /> Lưu ý: Hãy tải đề về trước khi đóng hoặc tải lại trang để tránh mất nội dung.</p>
      </section>}
    <footer className="home-footer"><span>ASTRA / Cùng thầy cô, mỗi ngày.</span><span>Một ý tưởng nhỏ. Một bài học hay.</span></footer></div></main>
  </div>;
};
