import React from 'react';
import type { ExamSession } from '../state/examSessions';
import { ArrowRight, FileText, SlidersHorizontal } from 'lucide-react';

interface OnboardingForkProps {
  onQuickMode: () => void;
  onProMode: () => void;
  sessions: ExamSession[];
  onOpenSession: (id: string) => void;
}

export const OnboardingFork: React.FC<OnboardingForkProps> = ({ onQuickMode, onProMode, sessions, onOpenSession }) => (
  <main className="home-screen">
    <div className="home-content">
      <div className="eyebrow">Không gian soạn đề · ASTRA</div>
      <h1>Không gian đề thi</h1>
      <p className="home-intro">Tạo đề mới hoặc tiếp tục công việc đang làm. Mỗi đề có nội dung và hội thoại riêng.</p>
      <div className="home-options">
        <button className="home-option home-option-primary" onClick={onQuickMode}>
          <div className="option-top"><FileText size={26} strokeWidth={1.5} /><span>Dễ bắt đầu</span></div>
          <h2>Tạo từ mẫu</h2>
          <p>Chọn môn học và cấu trúc đề có sẵn. ASTRA sẽ tạo các câu hỏi để bạn kiểm tra.</p>
          <div className="option-detail">Chọn cấu trúc đề → Chọn môn học</div>
          <div className="option-action">Chọn mẫu đề <ArrowRight size={19} /></div>
        </button>
        <button className="home-option" onClick={onProMode}>
          <div className="option-top"><SlidersHorizontal size={26} strokeWidth={1.5} /><span>Tùy chỉnh nội dung</span></div>
          <h2>Tạo theo yêu cầu</h2>
          <p>Mở không gian làm việc để mô tả chủ đề, mức độ và nội dung bạn muốn đưa vào đề.</p>
          <div className="option-detail">Nhập yêu cầu bằng ngôn ngữ tự nhiên</div>
          <div className="option-action">Mở không gian soạn đề <ArrowRight size={19} /></div>
        </button>
      </div>
      <div className="session-library">
        <SessionStack title="Tiếp tục đề đang soạn" sessions={sessions.filter(session => session.status !== 'complete')} onOpen={onOpenSession} empty="Chưa có đề đang soạn. Chọn một cách tạo đề ở phía trên để bắt đầu." />
        <SessionStack title="Đề đã soạn" sessions={sessions.filter(session => session.status === 'complete')} onOpen={onOpenSession} empty="Các đề tạo xong sẽ xuất hiện ở đây để bạn xem lại và xuất file." />
      </div>
      <p className="session-storage-note">Danh sách được giữ trong phiên làm việc hiện tại. Tải lại hoặc đóng trang sẽ xóa danh sách.</p>
    </div>
  </main>
);

function SessionStack({ title, sessions, onOpen, empty }: { title: string; sessions: ExamSession[]; onOpen: (id: string) => void; empty: string }) {
  return <section className="session-stack" aria-label={title}>
    <header className="stack-heading"><h2>{title}</h2><span>{sessions.length} đề</span></header>
    {sessions.length === 0 ? <p className="stack-empty">{empty}</p> : <ul className="session-list">
      {sessions.map(session => {
        const flagged = session.questions.filter(question => question.status === 'FLAGGED').length;
        return <li key={session.id}>
          <button className="session-row" onClick={() => onOpen(session.id)}>
            <FileText size={21} strokeWidth={1.5} className="session-row-icon" />
            <div className="session-row-main">
              <strong>{session.title}</strong>
              <span>{session.mode === 'template' ? 'Từ mẫu' : 'Theo yêu cầu'} · {session.meta ? `${session.meta.subject} · ${session.meta.duration} phút` : 'Chưa chọn môn học'} · {new Date(session.createdAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</span>
              {session.status === 'generating' && session.meta && <progress max={session.meta.totalCount} value={session.meta.completedCount} aria-label={`Tiến độ ${session.title}`} />}
            </div>
            <div className="session-row-state">
              <span className={session.status === 'error' || flagged ? 'session-warning' : ''}>{session.status === 'generating' ? `Đang tạo · ${session.meta?.completedCount || 0}/${session.meta?.totalCount || 0} câu` : session.status === 'complete' ? `${session.questions.length} câu${flagged ? ` · ${flagged} cần xem xét` : ' · Đã soạn xong'}` : session.status === 'error' ? 'Tạo đề chưa thành công' : 'Bản nháp'}</span>
              <span className="session-row-open">{session.status === 'complete' ? 'Mở đề' : 'Tiếp tục'} <ArrowRight size={16} /></span>
            </div>
          </button>
        </li>;
      })}
    </ul>}
  </section>;
}
