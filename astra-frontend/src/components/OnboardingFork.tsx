import React from 'react';
import { ArrowRight, FileText, SlidersHorizontal } from 'lucide-react';

interface OnboardingForkProps {
  onQuickMode: () => void;
  onProMode: () => void;
  hasActiveSession?: boolean;
  onResumeSession?: () => void;
}

export const OnboardingFork: React.FC<OnboardingForkProps> = ({ onQuickMode, onProMode, hasActiveSession, onResumeSession }) => (
  <main className="home-screen">
    <div className="home-content">
      <div className="eyebrow">Không gian soạn đề · ASTRA</div>
      <h1>Soạn đề thi mới</h1>
      <p className="home-intro">Từ ý tưởng đến một đề thi hoàn chỉnh.<br />Chọn cách bắt đầu, sau đó xem và kiểm tra từng câu hỏi.</p>
      {hasActiveSession && onResumeSession && (
        <section className="resume-session" aria-label="Phiên đang mở">
          <div><strong>Tiếp tục đề thi đang soạn</strong><p>Đề thi và hội thoại của bạn vẫn được giữ trong phiên này.</p></div>
          <button className="button-primary" onClick={onResumeSession}>Tiếp tục <ArrowRight size={17} /></button>
        </section>
      )}
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
      <ol className="home-steps" aria-label="Quy trình soạn đề">
        <li><span>01</span><div><strong>Chọn nội dung</strong><p>Môn học, cấu trúc và yêu cầu</p></div></li>
        <li><span>02</span><div><strong>Xem & kiểm tra</strong><p>Đọc đề và xem ghi chú kiểm định</p></div></li>
        <li><span>03</span><div><strong>Xuất đề thi</strong><p>Tách riêng đề và đáp án</p></div></li>
      </ol>
    </div>
  </main>
);
