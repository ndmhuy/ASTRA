import React from 'react';
import { Sparkles, CheckCircle2, BookOpen, Clock } from 'lucide-react';

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
      <div className="astra-header-inner">
        {/* Brand */}
        <div className="astra-brand" onClick={() => onNavigate('config')}>
          <div className="astra-logo-icon">
            <Sparkles className="w-5 h-5 text-emerald-700" />
          </div>
          <div>
            <div className="astra-brand-name">ASTRA</div>
            <div className="astra-brand-sub">Soạn & Kiểm Định Đề Thi</div>
          </div>
        </div>

        {/* 3 Clear Steps */}
        <nav className="astra-nav-links">
          <button
            onClick={() => onNavigate('config')}
            className={`astra-nav-item ${currentScreen === 'config' ? 'active' : ''}`}
          >
            <BookOpen className="w-4 h-4 mr-1.5" />
            <span>1. Soạn đề</span>
          </button>

          <span className="astra-nav-arrow">›</span>

          <button
            onClick={() => onNavigate('stepper')}
            disabled={currentScreen === 'config'}
            className={`astra-nav-item ${currentScreen === 'stepper' ? 'active' : ''}`}
          >
            <Clock className="w-4 h-4 mr-1.5" />
            <span>2. Tiến trình</span>
          </button>

          <span className="astra-nav-arrow">›</span>

          <button
            onClick={() => onNavigate('review')}
            disabled={!canNavigateToReview}
            className={`astra-nav-item ${currentScreen === 'review' ? 'active' : ''}`}
          >
            <CheckCircle2 className="w-4 h-4 mr-1.5" />
            <span>3. Xem & In đề</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
