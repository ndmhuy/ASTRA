import React from 'react';
import { Sparkles, CheckCircle2, BookOpen, Clock, ArrowLeft } from 'lucide-react';

interface NavbarProps {
  currentScreen: 'config' | 'stepper' | 'review';
  onNavigate: (screen: 'config' | 'stepper' | 'review') => void;
  canNavigateToReview: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentScreen,
  onNavigate,
  canNavigateToReview
}) => {
  return (
    <header className="astra-header">
      <div className="astra-header-container">
        {/* Logo and Brand */}
        <div className="astra-brand" onClick={() => onNavigate('config')} title="Về màn hình chính">
          <div className="astra-logo-icon">
            <Sparkles className="w-6 h-6 text-indigo-700" />
          </div>
          <div>
            <div className="astra-brand-title">
              ASTRA <span className="astra-badge-tag">Hỗ trợ giáo viên</span>
            </div>
            <div className="astra-brand-subtitle">
              Soạn & Thẩm định đề thi chuẩn GDPT
            </div>
          </div>
        </div>

        {/* Big Easy-to-Navigate Step Pills */}
        <nav className="astra-nav-steps">
          <button
            onClick={() => onNavigate('config')}
            className={`astra-step-btn ${currentScreen === 'config' ? 'active' : ''}`}
          >
            <BookOpen className="w-4 h-4" />
            <span>1. Soạn Đề</span>
          </button>

          <span className="astra-step-divider">›</span>

          <button
            onClick={() => onNavigate('stepper')}
            disabled={currentScreen === 'config'}
            className={`astra-step-btn ${currentScreen === 'stepper' ? 'active' : ''}`}
          >
            <Clock className="w-4 h-4" />
            <span>2. Tiến Trình</span>
          </button>

          <span className="astra-step-divider">›</span>

          <button
            onClick={() => onNavigate('review')}
            disabled={!canNavigateToReview}
            className={`astra-step-btn ${currentScreen === 'review' ? 'active' : ''}`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>3. Xem & In Đề</span>
          </button>

          {currentScreen === 'review' && (
            <button
              onClick={() => onNavigate('config')}
              className="astra-back-nav-btn ml-3"
              title="Soạn một đề thi mới"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              <span>Tạo đề mới</span>
            </button>
          )}
        </nav>
      </div>
    </header>
  );
};
