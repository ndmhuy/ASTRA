import { useEffect, useState } from 'react';
import { BookOpenCheck, PenLine } from 'lucide-react';
import { AstraLogo } from './AstraLogo';
import {
  AstrolabeMotif,
  CompassDivider,
  ConstellationMotif,
  CornerPlate,
  MathDraftingMotif,
} from './AtelierMotifs';
import { ModernChatBar } from './Workspace/ChatPane/ModernChatBar';

interface Props {
  exiting: boolean;
  draft: string;
  onDraftChange: (value: string) => void;
  onTemplate: () => void;
  onDetailed: () => void;
  onSend: (message: string, options: { searchWeb: boolean; attachedFiles: File[] }) => void;
}
export function WorkspaceStart({ exiting, draft, onDraftChange, onTemplate, onDetailed, onSend }: Props) {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let second = 0;
    const first = requestAnimationFrame(() => { second = requestAnimationFrame(() => setReady(true)); });
    return () => { cancelAnimationFrame(first); cancelAnimationFrame(second); };
  }, []);
  return <main className={`integrated-start ${ready ? 'is-ready' : ''} ${exiting ? 'is-exiting' : ''}`} aria-labelledby="workspace-greeting" inert={exiting}>
    <div className="start-atelier-decor" aria-hidden="true">
      <AstrolabeMotif className="start-decor-astrolabe" />
      <MathDraftingMotif className="start-decor-math" />
      <ConstellationMotif className="start-decor-constellation" />
      <CornerPlate className="start-decor-corner is-tl" />
      <CornerPlate className="start-decor-corner is-br" />
    </div>
    <div className="integrated-start-content">
      <div className="integrated-greeting">
        <AstraLogo className="integrated-greeting-logo" />
        <h1 id="workspace-greeting">Chào thầy cô!</h1>
        <p>Cùng ASTRA mở trang đề tiếp theo.</p>
      </div>
      <CompassDivider className="start-compass-divider" />
      <div className="integrated-start-actions">
        <button type="button" className="button-primary start-action-btn" onClick={onTemplate}><BookOpenCheck size={17} aria-hidden="true" />Soạn từ mẫu</button>
        <button type="button" className="button-secondary start-action-btn" onClick={onDetailed}><PenLine size={17} aria-hidden="true" />Soạn chi tiết</button>
      </div>
      <div className="integrated-start-composer"><ModernChatBar onSend={onSend} draft={draft} onDraftChange={onDraftChange} disabled={exiting} /></div>
      <p className="integrated-start-help">Chọn một cách bắt đầu, hoặc nhập ý tưởng ngay bên trên.</p>
      <p className="start-capabilities">
        <span>Toán THPT · 22 câu / 90 phút</span>
        <span aria-hidden="true">·</span>
        <span>ĐGNL V-ACT · 120 câu / 5 lĩnh vực</span>
        <span aria-hidden="true">·</span>
        <span>Kiểm định độc lập &amp; xem trước PDF</span>
      </p>
    </div>
  </main>;
}
