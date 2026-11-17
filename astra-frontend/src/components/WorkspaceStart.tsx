import { useEffect, useRef, useState } from 'react';
import { BookOpenCheck, PenLine } from 'lucide-react';
import { AstraLogo } from './AstraLogo';
import { ModernChatBar } from './Workspace/ChatPane/ModernChatBar';

interface Props {
  exiting: boolean;
  draft: string;
  onDraftChange: (value: string) => void;
  onTemplate: () => void;
  onSend: (message: string, options: { searchWeb: boolean; attachedFiles: File[] }) => void;
}
export function WorkspaceStart({ exiting, draft, onDraftChange, onTemplate, onSend }: Props) {
  const [ready, setReady] = useState(false);
  const [detailed, setDetailed] = useState(false);
  const container = useRef<HTMLElement>(null);
  useEffect(() => {
    let second = 0;
    const first = requestAnimationFrame(() => { second = requestAnimationFrame(() => setReady(true)); });
    return () => { cancelAnimationFrame(first); cancelAnimationFrame(second); };
  }, []);
  return <main ref={container} className={`integrated-start ${ready ? 'is-ready' : ''} ${exiting ? 'is-exiting' : ''}`} aria-labelledby="workspace-greeting" inert={exiting}>
    <div className="integrated-start-content">
      <div className="integrated-greeting"><AstraLogo className="integrated-greeting-logo" /><h1 id="workspace-greeting">Chào thầy cô!</h1><p>Cùng ASTRA mở trang đề tiếp theo.</p></div>
      <div className="integrated-start-actions">
        <button className="button-secondary" onClick={onTemplate}><BookOpenCheck size={18} aria-hidden="true" />Soạn từ mẫu</button>
        <button className="button-primary" onClick={() => { setDetailed(true); container.current?.querySelector('textarea')?.focus(); }}><PenLine size={18} aria-hidden="true" />Soạn chi tiết</button>
      </div>
      <div className="integrated-start-composer"><ModernChatBar onSend={onSend} draft={draft} onDraftChange={onDraftChange} disabled={exiting} /></div>
      <p className="integrated-start-help" role="status">{detailed ? 'Mô tả môn học, chủ đề, số câu và yêu cầu của thầy cô. Gửi để thiết lập và bắt đầu soạn.' : 'Chọn một cách bắt đầu, hoặc nhập ý tưởng ngay bên trên.'}</p>
    </div>
  </main>;
}
