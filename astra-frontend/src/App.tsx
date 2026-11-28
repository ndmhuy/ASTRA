import React, { useState, useEffect, useSyncExternalStore, useCallback, useLayoutEffect, useMemo, useRef } from 'react';
import { flushSync } from 'react-dom';
import { meaningful, recentQuestion, redact, retrievedContext, searchSessions } from './agent/memory';
import { interpretationUnavailable, interpret, researchAdjacentTopic } from './agent/client';
import { admit, execute, fastRoute, fold, type Effect, type Runtime } from './agent/recipes';
import { displayNumber, failure, inspectQuestion, previewText, resolveQuestion, sectionId, statusText, success } from './agent/examActions';
import type { Intent } from './agent/contracts';
import { activeGeneration, generationTarget, generationReceipt, generationJob, restingGeneration } from './agent/lifecycle';
import { workspaceDescription, workspaceContextFacts } from './agent/workspaceFacts';
import { readLiveState, liveStatusText } from './agent/liveState';
import { GOALS, PRACTICE_LIMITS, understandLocal, decisionMeaning, planMeaning } from './agent/intelligence';
import { reduceSpec, specDraft, patchSpec, specSummary, paramsForSpec } from './agent/examSpec';
import { familyFor, formatOverview, matchAdjacentTopic, mentionedFamilies, resolveIntake } from './agent/knowledge';
import { AlertCircle, AlertTriangle, LoaderCircle, PanelLeftClose, PanelLeftOpen, RefreshCw, Settings2 } from 'lucide-react';
import { WorkspaceStart } from './components/WorkspaceStart';
import { AstraWelcome } from './components/AstraWelcome';
import { ConnectionSetup } from './components/ConnectionSetup';
import { SidebarExamLibrary } from './components/SidebarExamLibrary';
import { AstraLogo } from './components/AstraLogo';
import { QuickPresetModal } from './components/QuickPresetModal';
import { WorkspaceLayout } from './components/Workspace/WorkspaceLayout';
import { ChatHistory } from './components/Workspace/ChatPane/ChatHistory';
import { ChatConfigCard } from './components/Workspace/ChatPane/ChatConfigCard';
import { ModernChatBar } from './components/Workspace/ChatPane/ModernChatBar';
import { CanvasHeader } from './components/Workspace/LiveCanvas/CanvasHeader';
import { ExamPaperView, type ExamCanvasViewMode, type ExamPaperControls } from './components/Workspace/LiveCanvas/ExamPaperView';
import type { InputDocument } from './services/inputDocuments';
import type { ChatMessage, ExamFormat, ExamRequestParams, QuestionItem, Subject } from './types/exam';
import { QuestionEditor, type QuestionEditorControls } from './components/QuestionEditor';
import { ApiError, evaluateExamFormat, examService, getExamFormats, type QuestionRegeneration } from './services/examService';
import { prepareParams, type Intake } from './agent/intake';
import { noteLabel, type Note } from './agent/notes';
import { ExamVersionHistory } from './components/ExamVersionHistory';
import { MathRenderer } from './components/MathRenderer';
import { ExamSessions } from './state/examSessions';
import { formatProgressStatus, formatVisualWarning } from './utils/userMessages.ts';
import './styles/workspace.css';
import './styles/classroom.css';
import './styles/studio.css';
import './styles/createVision.css';
import './styles/integratedWorkspace.css';
import './styles/integration.css';
import './styles/atelier.css';

interface RegenerationUndo {
  sessionId: string;
  jobId: string;
  previousRevision: number;
  revision: number;
}
type EditorTarget = { sessionId: string; jobId: string; question: QuestionItem; workspaceId?: string };
type QuestionRun = { id: string; target: EditorTarget; receipt?: QuestionRegeneration; stopping?: boolean };
const QUESTION_STAGES = {
  queued: [5, 'Đã xếp hàng'], composer: [25, 'Đang tạo lại'], illustrator: [50, 'Đang vẽ hình'],
  solver: [75, 'Đang kiểm tra'], saving: [95, 'Đang lưu'],
} as const;
const CONFIRMATION_TTL_MS = 5 * 60_000;

type Confirmation = {
  workspaceId: string;
  binding: string;
  expires: number;
  continuation?: Intent[];
  continuationMessage?: string;
  run: (sourceId?: string, uploadedFiles?: string[]) => Promise<Effect> | Effect;
};

export const App: React.FC = () => {
  const [showWelcome, setShowWelcome] = useState(true);
  const finishWelcome = useCallback(() => setShowWelcome(false), []);
  const [landingDraft, setLandingDraft] = useState('');
  const [landingDocuments, setLandingDocuments] = useState<InputDocument[]>([]);
  const [leavingStart, setLeavingStart] = useState(false);
  const [revealingWorkspace, setRevealingWorkspace] = useState(false);
  const transitionTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const composerOrigin = useRef<DOMRect | null>(null);
  const [store] = useState(() => new ExamSessions(examService));
  const sessions = useSyncExternalStore(store.subscribe, store.getSnapshot);
  const libraryError = useSyncExternalStore(store.subscribe, store.getLibraryError);
  const browserImport = useSyncExternalStore(store.subscribe, store.getBrowserImport);
  const turn = useRef<AbortController | null>(null);
  const [admissionError, setAdmissionError] = useState('');
  const pending = useRef<Confirmation | null>(null);
  const canvas = useRef<ExamPaperControls>(null);
  const editorControls = useRef<QuestionEditorControls>(null);
  const editorBusy = useRef(new Set<string>());
  const questionRuns = useRef(new Map<string, QuestionRun>());
  const [questionProgress, setQuestionProgress] = useState<Record<string, QuestionRun | undefined>>({});
  const [agentOpenedPdf, setAgentOpenedPdf] = useState(false);
  const presetDialog = useRef<HTMLDivElement>(null);
  const activeRef = useRef<string | null>(null);
  const runtimeRef = useRef<Runtime | null>(null);
  const [chatPending, setChatPending] = useState(false);
  const [catalogFormats, setCatalogFormats] = useState<ExamFormat[]>([]);
  const chatDrafts = useMemo(() => Object.fromEntries(sessions.map(session => [session.id,
    session.status==='draft' && !session.generationStopped ? specDraft(session.intake,catalogFormats) : undefined])), [sessions,catalogFormats]);
  const [pendingActionMeta, setPendingActionMeta] = useState<{ workspaceId: string; label: string; confirmLabel?: string } | null>(null);
  const [configureFormatId, setConfigureFormatId] = useState<string | undefined>(undefined);
  const setPendingConfirmation = useCallback(
    (confirmation: Confirmation | null, meta: { workspaceId: string; label: string; confirmLabel?: string } | null = null) => {
      pending.current = confirmation;
      setPendingActionMeta(confirmation ? meta : null);
    },
    []
  );
  const cancelTurn = () => {
    turn.current?.abort();
    turn.current = null;
    setPendingConfirmation(null);
    setChatPending(false);
  };
  useEffect(() => () => turn.current?.abort(), []);
  useEffect(() => {
    let mounted = true;
    void getExamFormats().then(items => {
      if (mounted) setCatalogFormats(items);
    }).catch(() => {});
    return () => { mounted = false; };
  }, []);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [screen, setScreen] = useState<'start' | 'workspace'>('start');
  const [viewMode, setViewMode] = useState<ExamCanvasViewMode>('paper');
  const [controlsCollapsed, setControlsCollapsed] = useState(false);
  const [showQuickModal, setShowQuickModal] = useState(false);
  const [agentSelection, setAgentSelection] = useState<{ formats: ExamFormat[]; id: string; expanded: boolean; summary?: string }>();
  const [configureId, setConfigureId] = useState<string | null>(null);
  const [editor, setEditor] = useState<EditorTarget | null>(null);
  const [approving, setApproving] = useState(false);
  const [verifyingQuestionId, setVerifyingQuestionId] = useState<number | null>(null);
  const [approvingQuestionId, setApprovingQuestionId] = useState<number | null>(null);
  const [historySession, setHistorySession] = useState<string | null>(null);
  const [undo, setUndo] = useState<RegenerationUndo>();
  const [undoing, setUndoing] = useState(false);
  const [undoConflict, setUndoConflict] = useState<{ id: string; current: string; afterChange: string; beforeChange: string }>();
  const closeQuickModal = useCallback(() => {
    turn.current?.abort();
    turn.current = null;
    setPendingConfirmation(null);
    setChatPending(false);
    setShowQuickModal(false);
    setAgentSelection(undefined);
    setConfigureFormatId(undefined);
  }, [setPendingConfirmation]);
  const active = sessions.find(session => session.id === activeId);
  const candidate = activeId ? questionProgress[activeId] : undefined;
  const questionRun = candidate?.target.jobId === active?.jobId ? candidate : undefined;
  const questionPending = questionRun && (!questionRun.receipt || questionRun.receipt.status === 'pending') ? questionRun : undefined;
  const questionStage = questionPending ? QUESTION_STAGES[questionPending.receipt?.stage ?? 'queued'] : undefined;
  const sharedId = active && !active.browserOnly && examService.workspaceLibrary ? active.id : null;
  const [recordedChat, setRecordedChat] = useState<{ id: string; messages: ChatMessage[]; signature: string }>();
  const history = examService.history;
  const canOpenHistory = Boolean(history && active?.jobId && active.package?.revision && active.status === 'complete');
  const canUndo = !sharedId && history && undo && active?.id === undo.sessionId && active.jobId === undo.jobId &&
    active.package?.revision === undo.revision;
  const messages = useMemo(() => {
    const recorded = recordedChat?.id === sharedId ? recordedChat.messages : [];
    const byId = new Map([...(active?.messages ?? []), ...recorded].map(message => [message.id, message]));
    return [...byId.values()].sort(
      (first, second) => Date.parse(first.timestamp) - Date.parse(second.timestamp)
    );
  }, [active?.messages, recordedChat, sharedId]);
  const latestUndo = sharedId && active?.package?.revision
    ? [...messages].reverse().find(message => message.changeId && message.examVersion?.jobId === active.jobId &&
        message.examVersion?.revision === active.package?.revision)
    : undefined;
  const liveQuestions = active?.questions || [];
  const isGenerating = active?.status === 'generating';
  const hasValidExam = Boolean(active && active.status !== 'error' && (active.package || liveQuestions.length > 0 || isGenerating));
  const examMeta = hasValidExam ? (active?.meta || null) : null;
  const prevQuestionCount = active?.previousCount || 0;
  useEffect(() => {
    store.resume();
    window.addEventListener('focus', store.loadLibrary);
    return () => {
      window.removeEventListener('focus', store.loadLibrary);
      store.dispose();
    };
  }, [store]);
  useEffect(() => {
    const library = examService.workspaceLibrary;
    if (!library || !sharedId || screen !== 'workspace') return;
    let current = true;
    let pending = false;
    const refresh = async () => {
      if (pending) return;
      pending = true;
      try {
        const { messages, milestones } = await library.changes(sharedId);
        if (current) {
          const timeline = [...messages, ...milestones];
          const signature = JSON.stringify(timeline);
          setRecordedChat(previous => previous?.id === sharedId && previous.signature === signature
            ? previous : { id: sharedId, messages: timeline, signature });
        }
      } catch {
        // Leave the last server-confirmed messages visible during a disconnect.
      } finally { pending = false; }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 1500);
    return () => { current = false; window.clearInterval(timer); };
  }, [screen, sharedId]);
  useEffect(() => {
    if (activeId && !active) {
      const importedId = store.importedWorkspaceId(activeId);
      setActiveId(importedId);
      if (!importedId) setScreen('start');
    }
  }, [activeId, active, store]);
  useEffect(() => {
    store.setActiveSession(screen === 'workspace' ? activeId : null);
  }, [store, screen, activeId]);
  useEffect(() => () => { if (transitionTimer.current) clearTimeout(transitionTimer.current); }, []);
  const cancelTransition = () => { composerOrigin.current = null; if (transitionTimer.current) clearTimeout(transitionTimer.current); setLeavingStart(false); setRevealingWorkspace(false); };
  const openSession = (id: string) => { cancelTransition(); setAgentOpenedPdf(false); setViewMode('paper'); setActiveId(id); setScreen('workspace'); };
  const openManually = (id: string) => { cancelTurn(); setAgentSelection(undefined); setShowQuickModal(false); setConfigureId(null); setConfigureFormatId(undefined); setEditor(null); openSession(id); };
  const newExam = () => { cancelTurn(); cancelTransition(); setActiveId(null); setConfigureId(null); setConfigureFormatId(undefined); setLandingDraft(''); setLandingDocuments([]); setAgentSelection(undefined); setShowQuickModal(false); setScreen('start'); };
  const revealSession = (id: string) => {
    if (screen === 'workspace') { openSession(id); return; }
    composerOrigin.current = document.querySelector('.integrated-start .composer-box')?.getBoundingClientRect() || null;
    setLeavingStart(true);
    transitionTimer.current = setTimeout(() => {
      setActiveId(id); setAgentOpenedPdf(false); setViewMode('paper'); setScreen('workspace'); setLeavingStart(false); setRevealingWorkspace(true);
      transitionTimer.current = setTimeout(() => setRevealingWorkspace(false), 420);
    }, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 180);
  };
  useLayoutEffect(() => {
    const from = composerOrigin.current;
    if (screen !== 'workspace' || !from) return;
    composerOrigin.current = null;
    const target = document.querySelector<HTMLElement>('.workspace-composer-slot .composer-box');
    if (!target || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const to = target.getBoundingClientRect();
    const animation = target.animate([{ transform: `translate(${from.left - to.left}px, ${from.top - to.top}px)`, width: `${from.width}px` }, { transform: 'translate(0, 0)', width: `${to.width}px` }], { duration: 360, easing: 'cubic-bezier(.2,.75,.25,1)' });
    return () => animation.cancel();
  }, [screen, activeId]);
  useLayoutEffect(() => {
    if (showWelcome || revealingWorkspace || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const view = document.querySelector<HTMLElement>(screen === 'workspace' ? '.astra-workspace-stage' : '.integrated-start');
    if (!view) return;
    const animation = view.animate([
      { opacity: 0, transform: 'translateY(8px)' },
      { opacity: 1, transform: 'translateY(0)' },
    ], { duration: 220, easing: 'cubic-bezier(.2,.75,.25,1)' });
    return () => animation.cancel();
    // Session updates and sidebar resizing must not replay the navigation animation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screen, activeId, showWelcome]);
  const handleDetailedStart = () => {
    const fromLanding = !configureId;
    const id = configureId || store.create('custom');
    store.setDraft(id, landingDraft);
    if (fromLanding) {
      if (landingDocuments.length) store.setInputDocuments(id, landingDocuments);
      setLandingDraft('');
      setLandingDocuments([]);
    }
    setShowQuickModal(false);
    setConfigureId(null);
    revealSession(id);
  };
  const confirmPending = async (sourceId?: string): Promise<Effect> => {
    const prepared=pending.current;
    setPendingConfirmation(null);
    if(!prepared || prepared.workspaceId!==activeRef.current) return failure('Hiện chưa có thao tác nào đang chờ xác nhận ở đề này.');
    if(prepared.expires<Date.now() || prepared.binding!==runtimeRef.current!.binding()) return failure('Xác nhận đã hết hiệu lực hoặc đề/cấu hình đã đổi. Hãy gửi lại yêu cầu.');
    const owned=!turn.current;
    const controller=turn.current??new AbortController();
    if(owned){turn.current=controller;setChatPending(true);}
    try {
      const effect=await prepared.run(sourceId);
      if(effect.status==='succeeded' && prepared.continuation?.length && !controller.signal.aborted) {
        const runtime:Runtime={binding:()=>runtimeRef.current!.binding(),dispatch:(...args)=>runtimeRef.current!.dispatch(...args)};
        const receipts=await execute(prepared.continuation,runtime,runtime.binding(),()=>!controller.signal.aborted,prepared.continuationMessage,sourceId);
        const consumed=receipts.length;
        if(receipts.at(-1)?.status==='pending' && pending.current) {pending.current.continuation=prepared.continuation.slice(consumed);pending.current.continuationMessage=prepared.continuationMessage;}
        return {...effect,text:[effect.text,...receipts.map(item=>item.text)].join('\n')};
      }
      return prepared.continuation?.length && effect.status!=='succeeded'?{...effect,text:effect.text+
        ` Còn ${prepared.continuation.length} bước trong yêu cầu “${redact(prepared.continuationMessage??'').slice(0,240)}” chưa thực hiện. Hãy chờ kết quả rồi yêu cầu tiếp tục; em sẽ kiểm tra lại đề và phiên bản trước khi làm.`}:effect;
    } finally {if(owned && turn.current===controller){turn.current=null;setChatPending(false);}}
  };
  const sendTurn = async (id: string, content: string, options: { searchWeb: boolean; attachedFiles: InputDocument[] }) => {
    if(turn.current)return;
    const admission=admit(content);
    setAdmissionError(admission.error??'');
    if(admission.error)return;
    content=admission.text;
    const controller=new AbortController();turn.current=controller;setChatPending(true);
    const messageId=crypto.randomUUID();
    const answer=(text:string)=>store.appendMessage(id,'assistant',text);
    let origin=store.getSnapshot().find(session=>session.id===id);
    const immediate=understandLocal(content,{formats:catalogFormats,intake:origin?.intake});
    let moved=false;
    if(immediate.kind!=='defer' && immediate.frame.dialogueAct!=='QUESTION' && immediate.frame.goals.some(goal=>!goal.prohibited&&['REQUEST_GENERATION','PREPARE_EXAM','PREPARE_PRACTICE'].includes(goal.goal)) &&
        (origin?.status==='complete'||origin?.status==='generating'||origin?.generationStopped||immediate.frame.goals.some(goal=>goal.parameters.fresh))) {
      const next=store.create('custom');
      flushSync(()=>openSession(next));id=next;origin=store.getSnapshot().find(session=>session.id===id);moved=true;
    }
    flushSync(()=>{store.setInputDocuments(id,options.attachedFiles);store.appendMessage(id,'user',content,messageId,true);});
    const sourceWorkspace=id;
    const alive=()=>!controller.signal.aborted && activeRef.current===id && !!store.getSnapshot().find(session=>session.id===sourceWorkspace)?.messages.some(item=>item.id===messageId);
    // A snapshot of the relevant entity, not every render/progress tick.
    const readBinding=()=>JSON.stringify([activeRef.current,store.getSnapshot().find(session=>session.id===id)?.jobId,
      store.getSnapshot().find(session=>session.id===id)?.package?.revision,store.getSnapshot().find(session=>session.id===id)?.intake]);
    const before=readBinding();
    const writeBefore=runtimeRef.current!.binding();
    try {
      const needsCatalog = immediate.kind === 'defer' || immediate.frame.goals.some(goal =>
        ['PREPARE_EXAM', 'REQUEST_GENERATION', 'READ_EXAM_STRUCTURE'].includes(goal.goal));
      const formats = catalogFormats.length || !needsCatalog
        ? catalogFormats : await getExamFormats();
      if(!alive())return;
      if (!catalogFormats.length && formats.length) setCatalogFormats(formats);
      const local = immediate.kind === 'defer' && formats !== catalogFormats
        ? understandLocal(content, { formats, intake: origin?.intake }) : immediate;
      origin=store.getSnapshot().find(session=>session.id===id);
      const interpreted=local.kind==='defer'?await interpret(id,messageId,redact(content),{
        screen,setup:showQuickModal,status:origin?.status??'draft',view:viewMode,
        ...(origin?retrievedContext(origin,messageId,content):{}),
        questionRefs:origin?[...new Set(origin.questions.map(q=>q.part??'').filter(Boolean))].slice(0,8):[],
        editor:Boolean(editor),approved:Boolean(origin?.package?.approved),preview:origin?.preview?.status??null,
        confirmationPending:pending.current?.workspaceId===id,
        grounded:{workspace:origin?.title?redact(origin.title).slice(0,120):undefined,lifecycle:origin?.progress?.status??origin?.status,
          spec:[...(origin?workspaceContextFacts(origin):[]),...specSummary(origin?.intake)].slice(0,8).map(redact),documents:(origin?.inputDocuments??[]).slice(0,5).map(doc=>redact(`${doc.filename} (${doc.kind}, ${doc.characters} characters)`).slice(0,240)),
          capabilities:formats.filter(format=>format.available).slice(0,12).map(format=>format.displayName.slice(0,80)),
          revision:origin?.package?.revision,pending:pendingActionMeta?.label?redact(pendingActionMeta.label).slice(0,240):undefined,itemRegeneration:Boolean(questionPending),searchWeb:options.searchWeb},
      },controller.signal):local.frame;
      if(!alive())return;
      const frame='dialogueAct' in interpreted?interpreted:decisionMeaning(interpreted,formats,origin?.intake);
      if(!frame){
        setPendingConfirmation(null);
        const explanation='reasonCode' in interpreted?interpretationUnavailable(interpreted.reasonCode):'Mình chưa xác định được thao tác bạn muốn thực hiện.';
        const state=await runtimeRef.current!.dispatch({id:'STATUS',args:{scope:'current'}},runtimeRef.current!.binding(),content,messageId);
        if(alive())answer(`${explanation}\n\n${state.text}`);
        return;
      }
      if(frame.dialogueAct==='CORRECT'||frame.constraints.some(item=>['NO_GENERATION','NO_WEB','NO_EXECUTION','NEGATED','CONTRADICTORY'].includes(item)))setPendingConfirmation(null);
      const plan=planMeaning(frame,recentQuestion(origin),origin?.status==='draft'?origin.intake?.missing:undefined);
      if(plan.kind==='confirm'){answer((await confirmPending(messageId)).text);return;}
      if(plan.kind==='cancel'){setPendingConfirmation(null);if(origin?.intake)store.setIntake(id,{...origin.intake,visible:false});answer('Đã hủy yêu cầu trò chuyện đang chờ. Phiên tạo đề giữ trạng thái hiện tại.');return;}
      if(plan.kind==='text'){
        if(!['QUESTION','CONVERSATION','GUIDANCE'].includes(frame.dialogueAct))setPendingConfirmation(null);
        const state=frame.dialogueAct==='INFORM'&&origin&&generationJob(origin)?await runtimeRef.current!.dispatch({id:'STATUS',args:{scope:'current'}},runtimeRef.current!.binding(),content,messageId):undefined;
        if(alive())answer(plan.text+(state?`\n\n${state.text}`:''));return;
      }
      const readOnly=plan.kind==='inspect'||(plan.kind==='intake'&&plan.information)||
        (plan.kind==='task'&&plan.intents.every(intent=>Object.values(GOALS).some(def=>'capability' in def&&def.capability===intent.id&&def.effect==='read')));
      const freshRead=plan.kind==='task'&&plan.intents.every(intent=>['STATUS','RECALL','LIST_SESSIONS','RECOVERABLE_JOBS','SHOW_FORMATS','LIST_DOCUMENTS','LIST_VERSIONS'].includes(intent.id));
      if(readBinding()!==before&&!freshRead){answer('Đề hoặc cấu hình đích đã thay đổi. Hãy chỉ rõ lại nội dung muốn xem hoặc sửa.');return;}
      if(!readOnly || frame.dialogueAct==='CORRECT')setPendingConfirmation(null);
      if(!readOnly && runtimeRef.current!.binding()!==writeBefore){answer('Đề, cấu hình hoặc trình chỉnh sửa đã thay đổi. Hãy gửi lại yêu cầu để xác nhận đúng trạng thái mới.');return;}
      if(plan.kind==='intake') {
        const spec=reduceSpec(origin?.intake,plan.proposal,formats,messageId);
        let chosen=formats.find(format=>format.id===spec.formatId);
        if(plan.information){
          const matches=formats.filter(format=>format.available&&(!spec.family||familyFor(format)===spec.family)&&(!spec.subject||format.subjects.some(subject=>subject===spec.subject)));
          answer(matches.length?matches.map(formatOverview).join('\n'):`Chưa có mẫu cho ${spec.subject??spec.family??'yêu cầu này'}. Mẫu đang hỗ trợ: ${formats.filter(format=>format.available).map(format=>format.displayName).join(', ')}.`);return;
        }
        if(editor){answer('Hãy hoàn tất câu đang chỉnh sửa trước khi đổi cấu hình đề.');return;}
        if(!moved && origin && (origin.status==='complete'||plan.proposal.fresh || origin.status==='generating'||origin.generationStopped)) {
          const newId=store.create('custom');
          flushSync(()=>{store.setInputDocuments(newId,options.attachedFiles);store.moveUserTurn(id,newId,messageId);openSession(newId);});
          id=newId;origin=store.getSnapshot().find(session=>session.id===id);
        }
        const next=reduceSpec(origin?.intake,plan.proposal,formats,messageId);
        chosen=formats.find(format=>format.id===next.formatId);
        flushSync(()=>store.setIntake(id,next));
        const draft=specDraft(next,formats)!;
        if(!chosen || !next.formatId){answer(`Chưa có mẫu cụ thể cho ${next.subject??next.family??'yêu cầu này'}. ${draft.needsClarification.join(' ')} Mẫu đang có: ${formats.filter(format=>format.available).map(format=>format.displayName).join(', ')}.`);return;}
        store.suggestTitle(id,`Đề ${chosen.displayName}`,messageId,3);
        answer(`Đã cập nhật cấu hình ${chosen.displayName}. ${draft.limitations.join(' ')}${next.topic?` Chủ đề: ${next.topic}.`:''}${next.difficulty?` Độ khó: ${next.difficulty}.`:''}${frame.goals.some(goal=>!goal.prohibited&&goal.goal==='READ_EXAM_STRUCTURE')?` ${formatOverview(chosen)}`:''} Kiểm tra thẻ cấu hình rồi bấm “${draft.hasMismatch?'Dùng mẫu này':'Tạo đề ngay'}”.`);
        // Confirmation uses a fingerprint of the visible spec and documents. Any edit revokes it.
        const {params}=paramsForSpec(next,formats,origin?.inputDocuments??[]);
        if(params&&!frame.constraints.includes('NO_GENERATION'))setPendingConfirmation({workspaceId:id,binding:runtimeRef.current!.binding(),expires:Date.now()+CONFIRMATION_TTL_MS,run:async()=> {
          const latest=store.getSnapshot().find(session=>session.id===id);
          const fresh=specDraft(latest?.intake,formats);
          if(!fresh)return failure('Cấu hình không còn hiệu lực.');
          const {params:currentParams,error:problem}=paramsForSpec(latest?.intake,formats,latest?.inputDocuments??[]);
          if(!currentParams)return failure(problem??'Mẫu đề không còn khả dụng.');
          const job=await store.generate(id,currentParams);
          return job?{status:'accepted',text:'Backend đã nhận công việc tạo đề. Hãy theo dõi tiến độ.'}:failure(store.getSnapshot().find(session=>session.id===id)?.error??'Chưa nhận được công việc.');
        }});
        return;
      }
      if(plan.kind==='inspect'){
        const current=store.getSnapshot().find(session=>session.id===id);
        answer(plan.targets.map(args=>inspectQuestion(current,args).text).join('\n'));
        for(const args of plan.targets){const q=current&&resolveQuestion(current,args);if(q?.stableId&&current?.jobId&&current.package?.revision)store.rememberQuestion(id,q.stableId,current.jobId,current.package.revision,messageId);}
        return;
      }
      if(plan.kind==='practice'&&!moved&&origin&&(origin.status==='complete'||origin.status==='generating'||origin.generationStopped)){
        const next=store.create('custom');
        flushSync(()=>{store.setInputDocuments(next,options.attachedFiles);store.moveUserTurn(id,next,messageId);openSession(next);});
        id=next;origin=store.getSnapshot().find(session=>session.id===id);
      }
      const intents=plan.kind==='practice'?[{id:'PREPARE_PRACTICE',args:{...plan.parameters,
        ...(frame.constraints.includes('NO_GENERATION')?{prepareOnly:true}:{}),
        ...(!plan.parameters.sourcePreference&&['no_web','attachments'].includes(origin?.intake?.sourcePreference??'')?{sourcePreference:origin!.intake!.sourcePreference!}:
          !plan.parameters.sourcePreference&&options.searchWeb&&!frame.constraints.includes('NO_WEB')?{sourcePreference:'web'}:{})}} as Intent]:plan.intents;
      const runtime:Runtime={binding:()=>runtimeRef.current!.binding(),dispatch:(...args)=>runtimeRef.current!.dispatch(...args)};
      const receipts=await execute(intents,runtime,runtime.binding(),()=>!controller.signal.aborted,content,messageId);
      if(controller.signal.aborted)return;
      if(receipts.at(-1)?.status==='pending' && pending.current) {pending.current.continuation=intents.slice(receipts.length);pending.current.continuationMessage=content;}
      answer([...receipts.map(item=>item.text),...(receipts.length<intents.length?[
        `Còn ${intents.length-receipts.length} bước trong yêu cầu này chưa thực hiện. ${pending.current?'Các bước phụ thuộc đang chờ xác nhận.':'Hãy kiểm tra kết quả bước hiện tại trước khi yêu cầu tiếp tục.'}`]:[])].join('\n') || 'Chưa thực hiện thao tác.');
    } catch(error) {
      setPendingConfirmation(null);
      if(!controller.signal.aborted)answer(error instanceof ApiError?error.message:error instanceof Error&&error.message.startsWith('agent_')?
        'Dịch vụ hiểu yêu cầu chưa trả lời hợp lệ. Chưa thay đổi cấu hình hay gửi yêu cầu tạo đề; thầy cô có thể dùng các nút trên giao diện.':'Chưa xác định được kết quả. Hãy kiểm tra trạng thái trước khi thử lại.');
    } finally {if(turn.current===controller){turn.current=null;setChatPending(false);}}
  };
  const handleLandingSend = (content: string, options: { searchWeb: boolean; attachedFiles: InputDocument[] }) => {
    if (turn.current) return;
    const admission = admit(content);
    setAdmissionError(admission.error || '');
    if (admission.error) return;
    const id = configureId || store.create('custom');
    flushSync(() => { setLandingDraft(''); setLandingDocuments([]); openSession(id); });
    void sendTurn(id, content, options);
  };
  const handleQuickStart = (params: ExamRequestParams) => {
    if (agentSelection?.summary) {
      const prepared = pending.current;
      pending.current = null;
      if (prepared?.workspaceId && prepared.workspaceId === configureId &&
          prepared.expires >= Date.now() && prepared.binding === runtimeRef.current?.binding() &&
          params.formatId === agentSelection.id) {
        void Promise.resolve(prepared.run(undefined, params.uploadedFiles)).then(effect => store.appendMessage(prepared.workspaceId, 'assistant', effect.text));
      } else {
        setAdmissionError('Xác nhận đã hết hiệu lực. Thầy cô hãy đóng cấu hình và gửi lại yêu cầu.');
      }
      return;
    }
    pending.current = null;
    const fromLanding = !configureId;
    const id = configureId || store.create('template');
    const session = store.getSnapshot().find(item => item.id === id);
    if(session?.intake && params.formatId)store.setIntake(id,patchSpec(session.intake,{formatId:params.formatId},catalogFormats));
    const instructions = session?.intake ? undefined : session?.messages.filter(message => message.role === 'user' && !message.agentTurn).map(message => message.content).join('\n');
    setShowQuickModal(false);
    revealSession(id);
    setAgentSelection(undefined);
    if (fromLanding) {
      if (landingDocuments.length) store.setInputDocuments(id, landingDocuments);
      setLandingDraft('');
      setLandingDocuments([]);
    }
    void store.generate(id, { ...params, prompt: instructions ? `${params.prompt}\n${instructions}` : params.prompt });
  };
  const handleSendMessage = (content: string, options: { searchWeb: boolean; attachedFiles: InputDocument[] }) => {
    if (activeId) void sendTurn(activeId, content, options);
  };
  const regenerateQuestion = async (
    sessionId: string, jobId: string, question: QuestionItem, instruction: string, workspaceId?: string,
  ) => {
    const previousRevision = question.examRevision;
    const regenerated = await examService.regenerateQuestion(
      jobId, question.id, instruction, previousRevision, workspaceId, question.stableId,
    );
    if (previousRevision !== undefined && regenerated.examRevision === previousRevision + 1) {
      setUndo({ sessionId, jobId, previousRevision, revision: regenerated.examRevision });
    }
  };
  const showQuestionRun = (id: string, run?: QuestionRun) => {
    setQuestionProgress(previous => ({ ...previous, [id]: run }));
  };

  const acceptQuestionReceipt = async (run: QuestionRun, receipt: QuestionRegeneration) => {
    const { sessionId, jobId, question } = run.target;
    if (questionRuns.current.get(sessionId) !== run) return;
    run.receipt = receipt;
    if (receipt.status === 'pending') {
      showQuestionRun(sessionId, { ...run });
      return;
    }
    questionRuns.current.delete(sessionId);
    showQuestionRun(sessionId, receipt.status === 'cancelled' ? { ...run } : undefined);
    try {
      if (receipt.status === 'completed') {
        if (receipt.afterRevision && question.examRevision !== undefined) {
          setUndo({ sessionId, jobId, previousRevision: question.examRevision, revision: receipt.afterRevision });
        }
        if (store.getSnapshot().find(session => session.id === sessionId)?.jobId === jobId) {
          store.invalidatePreview(sessionId);
          await store.refresh(sessionId);
        }
      } else if (receipt.error) {
        await store.handleActionError(sessionId, new ApiError(receipt.error.message, receipt.error.code));
      }
    } catch (error) {
      await store.handleActionError(sessionId, error);
    } finally {
      editorBusy.current.delete(sessionId);
    }
  };

  const startQuestionRun = async (target: EditorTarget, instruction: string) => {
    const api = examService.questionRegeneration;
    if (!api) { await editQuestion(target, 'regen', instruction); return; }
    const { sessionId, jobId, question, workspaceId } = target;
    if (editorBusy.current.has(sessionId)) throw new Error('Đang xử lý một thao tác chỉnh sửa.');
    const run: QuestionRun = { id: crypto.randomUUID(), target };
    editorBusy.current.add(sessionId);
    questionRuns.current.set(sessionId, run);
    showQuestionRun(sessionId, { ...run });
    setEditor(current => current === target ? null : current);
    try {
      await acceptQuestionReceipt(run, await api.start(jobId, run.id, question, instruction, workspaceId));
      while (questionRuns.current.get(sessionId) === run) {
        await new Promise(resolve => window.setTimeout(resolve, 500));
        if (questionRuns.current.get(sessionId) !== run) break;
        await acceptQuestionReceipt(run, await api.status(jobId, run.id));
      }
    } catch (error) {
      if (questionRuns.current.get(sessionId) !== run) return;
      questionRuns.current.delete(sessionId);
      editorBusy.current.delete(sessionId);
      showQuestionRun(sessionId);
      await store.handleActionError(sessionId, error);
    }
  };

  const stopQuestionRun = async (sessionId: string) => {
    const run = questionRuns.current.get(sessionId);
    const api = examService.questionRegeneration;
    if (!run?.receipt || run.stopping || !api) return;
    run.stopping = true;
    showQuestionRun(sessionId, { ...run });
    try {
      await acceptQuestionReceipt(run, await api.stop(run.target.jobId, run.id));
    } catch (error) {
      if (questionRuns.current.get(sessionId) !== run) return;
      run.stopping = false;
      showQuestionRun(sessionId, { ...run });
      await store.handleActionError(sessionId, error);
    }
  };
  const exportFile = async (type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: 'tex' | 'pdf' | 'json' | 'docx' | 'md') => {
    const session = active;
    if (!session?.jobId) return false;
    try {
      await examService.downloadExport(
        session.jobId, type, format, session.meta?.title || session.package?.title || session.title,
      );
      return true;
    }
    catch (error) { await store.handleActionError(session.id, error); return false; }
  };
  const approve = async () => {
    const session = active;
    if (!session?.jobId || !session.package || !examService.approveExam || !store.canApprove(session.id)) return false;
    setApproving(true);
    try {
      await examService.approveExam(session.jobId, session.package);
      await store.refresh(session.id);
      return store.getSnapshot().find(item => item.id === session.id)?.package?.approved === true;
    } catch (error) {
      await store.handleActionError(session.id, error);
      return false;
    }
    finally { setApproving(false); }
  };
  const handleVerifyQuestion = async (questionId: number) => {
    const session = active;
    if (!session?.jobId || session.package?.revision === undefined || !examService.verifyQuestion) return;
    setVerifyingQuestionId(questionId);
    try {
      await examService.verifyQuestion(session.jobId, questionId, session.package.revision);
      await store.refresh(session.id);
    } catch (error) {
      await store.handleActionError(session.id, error);
    } finally {
      setVerifyingQuestionId(current => (current === questionId ? null : current));
    }
  };
  const handleApproveQuestion = async (questionId: number, reason = '') => {
    const session = active;
    if (!session?.jobId || session.package?.revision === undefined || !examService.approveQuestion) return;
    setApprovingQuestionId(questionId);
    try {
      const updated = await examService.approveQuestion(
        session.jobId,
        questionId,
        session.package.revision,
        reason,
        'local-teacher',
      );
      store.acceptPackage(session.id, updated.examId, updated);
    } catch (error) {
      await store.handleActionError(session.id, error);
      throw error;
    } finally {
      setApprovingQuestionId(current => (current === questionId ? null : current));
    }
  };
  const handlePreviewOpened = useCallback(() => {
    if (activeId && !agentOpenedPdf) store.markPreviewOpened(activeId);
  }, [store, activeId, agentOpenedPdf]);
  const openPdfManually = () => { setAgentOpenedPdf(false); setViewMode('pdf'); };
  const handleRetryPreview = useCallback(() => {
    if (activeId) void store.requestPreview(activeId, true);
  }, [store, activeId]);

  const restoreVersion = async (sessionId: string, jobId: string, version: number, revision: number,
    workspaceId?: string, targetJobId?: string) => {
    if (!history) return;
    try {
      const pkg = await history.restore(jobId, version, revision, workspaceId, targetJobId);
      if (pkg.examId !== jobId) await store.loadLibrary();
      store.acceptPackage(sessionId, pkg.examId, pkg);
      setViewMode('paper');
      setUndo(previous => previous?.sessionId === sessionId ? undefined : previous);
    } catch (error) {
      await store.handleActionError(sessionId, error);
      throw error;
    }
  };

  const undoRegeneration = async () => {
    if (!canUndo || !undo || undoing) return;
    setUndoing(true);
    try { await restoreVersion(undo.sessionId, undo.jobId, undo.previousRevision, undo.revision); }
    catch { /* The workspace shows the restore error. */ }
    finally { setUndoing(false); }
  };

  const undoRecordedChange = async (message: ChatMessage) => {
    const library = examService.workspaceLibrary;
    const revision = active?.package?.revision;
    if (!library || !sharedId || !revision || !message.changeId || !message.examVersion || undoing) return;
    setUndoing(true);
    setUndoConflict(undefined);
    try {
      const pkg = await library.undoChange(sharedId, message.examVersion.jobId, message.changeId, revision);
      store.acceptPackage(sharedId, pkg.examId, pkg);
      setViewMode('paper');
    } catch (error) {
      if (error instanceof ApiError && error.code === 'exam_undo_conflict' && error.details) {
        const comparison = error.details as { current: string; afterChange: string; beforeChange: string };
        setUndoConflict({ id: sharedId, ...comparison });
      } else {
        await store.handleActionError(sharedId, error);
      }
    } finally { setUndoing(false); }
  };

  const branchFromMessage = async (id: string, message: ChatMessage) => {
    try {
      let branchId: string | null;
      try { branchId = await store.branchAtMessage(id, message.id); }
      catch (error) {
        if (!(error instanceof ApiError) || error.code !== 'branch_version_unknown') throw error;
        if (!window.confirm('Tin nhắn này chưa có phiên bản đã lưu. Tạo nhánh từ đề đang dùng?')) return;
        branchId = await store.branchAtMessage(id, message.id, true);
      }
      if (branchId) openSession(branchId);
    } catch (error) {
      await store.handleActionError(id, error);
    }
  };

  const editQuestion = async (target: EditorTarget, kind: 'save' | 'verify' | 'regen', value?: QuestionItem | string) => {
    if (editorBusy.current.has(target.sessionId)) throw new Error('Đang xử lý một thao tác chỉnh sửa.');
    editorBusy.current.add(target.sessionId);
    try {
      if (kind === 'save') await examService.updateQuestion(target.jobId, value as QuestionItem, target.workspaceId);
      else if (kind === 'regen') await regenerateQuestion(
        target.sessionId, target.jobId, target.question, value as string, target.workspaceId,
      );
      else if (examService.verifyQuestion && target.question.examRevision !== undefined) {
        await examService.verifyQuestion(target.jobId, target.question.id, target.question.examRevision);
      } else throw new Error('Tính năng kiểm tra lại hiện chưa sẵn sàng.');
      if (kind !== 'verify') store.invalidatePreview(target.sessionId);
      await store.refresh(target.sessionId);
      setEditor(current => current?.sessionId === target.sessionId && current?.question.id === target.question.id ? null : current);
      return store.getSnapshot().find(session => session.id === target.sessionId);
    } catch (error) {
      await store.handleActionError(target.sessionId, error);
      throw error;
    } finally {
      editorBusy.current.delete(target.sessionId);
    }
  };

  const binding = () => {
    const current = store.getSnapshot().find(s => s.id === activeId);
    return JSON.stringify([screen, activeId, showQuickModal, configureId, controlsCollapsed, viewMode,
      editor?.question.stableId, current?.status, current?.jobId, current?.package?.revision,
      editorControls.current?.snapshot(), current?.package?.contentHash, current?.package?.approved, current?.previewOpenedRevision,
      current?.preview?.status, current?.artifactChanged,
      agentSelection?.id, agentSelection?.formats.find(format => format.id === agentSelection?.id)?.version,
      current?.intake, current?.notes, current?.progress?.executionVersion, current?.inputDocuments?.map(doc=>[doc.id,doc.sha256]),
      current?.conversation?.questionReference,
      store.getSnapshot().map(item => [item.id, item.title])]);
  };
  const dispatch = (intent: Intent, expected?: string, message = '', messageId = '', resolved?: Intake): Effect | Promise<Effect> => {
    const failed = failure;
    const succeeded = success;
    const current = store.getSnapshot().find(session => session.id === activeId);
    const activeTurn = turn.current;
    const validTurn = () => !!activeTurn && turn.current === activeTurn && !activeTurn.signal.aborted;
    const prepare = (text: string, run: Confirmation['run'], confirmLabel = 'Xác nhận'): Effect => {
      if (!current) return failed('Hãy mở không gian soạn đề trước.');
      setPendingConfirmation({ workspaceId: current.id, binding: binding(), expires: Date.now() + CONFIRMATION_TTL_MS, run }, {
        workspaceId: current.id, label: text, confirmLabel,
      });
      return { status: 'pending', text: `${text} Bấm “${confirmLabel}” bên dưới hoặc nhắn “Xác nhận”.` };
    };
    switch (intent.id) {
      case 'UPLOAD_GUIDANCE':
        return succeeded('Dùng nút Đính kèm tài liệu trên ô nhập, chọn loại tài liệu rồi chọn tệp. Em không thể tự mở hộp chọn tệp hay đọc tệp chưa tải lên.');
      case 'LIST_DOCUMENTS': {
        const docs=current?.inputDocuments??[];
        const name=typeof intent.args.name==='string'?fold(intent.args.name):'';
        const selected=name?docs.filter(doc=>fold(doc.filename)===name):docs;
        return succeeded(selected.length?selected.map(doc=>`${doc.filename} · ${doc.kind} · ${doc.characters} ký tự${name?`\nTrích đoạn đã lưu: ${doc.preview}`:''}`).join('\n'):'Chưa có tài liệu phù hợp gắn với đề này.');
      }
      case 'DETACH_DOCUMENT': {
        const docs=current?.inputDocuments??[];
        const matches=docs.filter(doc=>fold(doc.filename)===fold(String(intent.args.name)));
        if(!current||matches.length!==1)return failed('Hãy ghi đúng tên một tài liệu đang đính kèm: '+docs.map(doc=>doc.filename).join(', '));
        const document=matches[0];
        return prepare(`Gỡ ${document.filename} khỏi cấu hình đề này.`,()=>{
          const latest=store.getSnapshot().find(session=>session.id===current.id);
          if(!latest?.inputDocuments?.some(doc=>doc.id===document.id))return failed('Tài liệu đã thay đổi.');
          store.setInputDocuments(current.id,latest.inputDocuments.filter(doc=>doc.id!==document.id));
          return succeeded('Đã gỡ tài liệu khỏi cấu hình của đề này.');
        });
      }
      case 'USE_DOCUMENT': {
        if(!current)return failed('Hãy mở đề có tài liệu trước.');
        const docs=current.inputDocuments??[];
        const matches=docs.filter(doc=>fold(doc.filename)===fold(String(intent.args.name)));
        if(matches.length!==1)return failed('Cần đúng một tài liệu đính kèm. Tài liệu đang có: '+(docs.map(doc=>doc.filename).join(', ')||'chưa có'));
        const spec=reduceSpec(current.intake,{mode:'request',sourcePreference:'attachments'},catalogFormats,messageId);
        const document=matches[0];
        store.setIntake(current.id,{...spec,documentIds:intent.args.exclusive?[document.id]:[...new Set([...(spec.documentIds??[]),document.id])]});
        return succeeded(`Đã chọn “${document.filename}” làm nguồn cho cấu hình đề. Chưa đọc ngoài trích đoạn đã lưu và chưa tạo nội dung mới.`);
      }
      case 'ITEM_REGENERATION_STATUS': {
        const run=current?questionRuns.current.get(current.id):undefined;
        if(!run || run.target.jobId!==current?.jobId)return succeeded('Không có lượt tạo lại câu hỏi đang được theo dõi ở đề này.');
        return succeeded(run.receipt?.status==='pending'?`Đang ${QUESTION_STAGES[run.receipt.stage??'queued'][1].toLowerCase()}.`:run.receipt?.status==='completed'?'Backend đã hoàn tất lượt tạo lại câu hỏi.':run.receipt?.status==='cancelled'?'Backend đã xác nhận hủy lượt tạo lại.':run.receipt?.status==='failed'?'Lượt tạo lại câu hỏi đã lỗi.':'Đang chờ Backend xác nhận trạng thái lượt tạo lại.');
      }
      case 'STOP_ITEM_REGENERATION': {
        const run=current?questionRuns.current.get(current.id):undefined;
        if(!current||!run||run.target.jobId!==current.jobId||run.receipt?.status!=='pending')return failed('Không có lượt tạo lại câu hỏi đang chạy ở đề này.');
        return stopQuestionRun(current.id).then(()=>{
          const after=questionRuns.current.get(current.id)?.receipt;
          return after?.status==='cancelled'?succeeded('Backend đã xác nhận hủy lượt tạo lại câu hỏi.'):{status:'pending',text:'Đã gửi yêu cầu dừng lượt tạo lại câu hỏi; đang chờ trạng thái Backend.'};
        });
      }
      case 'LIST_VERSIONS':
      case 'INSPECT_VERSION':
      case 'RESTORE_VERSION': {
        if(!history||!current?.jobId||!current.package?.revision)return failed('Cần mở đề có phiên bản đã lưu.');
        if(intent.args.title && fold(String(intent.args.title))!==fold(current.title))return failed('Hãy mở đúng đề trước khi đọc hoặc khôi phục lịch sử của đề đó.');
        const jobId=current.jobId, revision=current.package.revision;
        return history.list(jobId,current.browserOnly?undefined:current.id).then(async list=>{
          if(!validTurn()||runtimeRef.current!.binding()!==expected)return failed('Đề hoặc phiên bản đã thay đổi.');
          const versions=list.versions;
          if(intent.id==='LIST_VERSIONS')return succeeded(versions.map(item=>`Phiên bản ${item.revision} · ${item.createdAt} · ${item.change}${(item.jobId??jobId)===jobId&&item.revision===revision?' · đang dùng':''}`).join('\n')||'Chưa có lịch sử phiên bản.');
          const ordered=versions.slice().sort((a,b)=>a.createdAt.localeCompare(b.createdAt)||a.revision-b.revision);
          const currentIndex=ordered.findIndex(item=>(item.jobId??jobId)===jobId&&item.revision===revision);
          const candidates=intent.args.version!==undefined?versions.filter(item=>item.revision===intent.args.version):intent.args.relative==='initial'?ordered.slice(0,1):intent.args.relative==='previous'&&currentIndex>0?ordered.slice(currentIndex-1,currentIndex):[];
          if(candidates.length!==1)return failed('Chưa xác định duy nhất phiên bản. Hãy xem danh sách lịch sử rồi nêu số phiên bản; các lần tạo có thể trùng số.');
          const target=candidates[0],targetJob=target.jobId??jobId;
          const pkg=await history.read(targetJob,target.revision);
          if(!validTurn()||runtimeRef.current!.binding()!==expected)return failed('Đề đã thay đổi khi đọc lịch sử.');
          if(intent.id==='INSPECT_VERSION')return succeeded(`Phiên bản ${target.revision} · ${target.createdAt} · ${pkg.questions.length} câu. Chưa khôi phục.\n`+
            pkg.questions.slice(0,6).map(q=>`${q.part??''} Câu ${displayNumber(q)}: ${q.stem}`).join('\n')+(pkg.questions.length>6?'\nĐây là 6 câu đầu; mở Lịch sử phiên bản để xem toàn bộ.':''));
          if(!target.restorable)return failed('Phiên bản này không còn đủ tệp nguồn để khôi phục.');
          return prepare(`Khôi phục phiên bản ${target.revision} (${target.createdAt}); bản mới cần được duyệt lại.`,async()=>{
            await restoreVersion(current.id,jobId,target.revision,revision,current.browserOnly?undefined:current.id,targetJob);
            return succeeded('Đã khôi phục phiên bản đã chọn. Hãy kiểm tra và duyệt lại.');
          });
        });
      }
      case 'UNDO_CHANGE': {
        if(!current?.package?.revision || !latestUndo || current.id!==sharedId)return failed('Không có thay đổi đủ điều kiện hoàn tác ở phiên bản hiện tại. Hãy xem lịch sử.');
        const change=latestUndo;
        return prepare('Hoàn tác thay đổi đã ghi nhận gần nhất của phiên bản hiện tại.',async()=>{
          const before=current.package?.revision;
          await undoRecordedChange(change);
          return store.getSnapshot().find(session=>session.id===current.id)?.package?.revision!==before?succeeded('Đã lưu phiên bản hoàn tác.'):failed('Chưa xác nhận hoàn tác; hãy kiểm tra cảnh báo xung đột và lịch sử.');
        });
      }
      case 'SAVE_EDITOR': {
        if(!editor||editor.sessionId!==current?.id||!editorControls.current)return failed('Hãy mở và kiểm tra bản nháp câu hỏi trước.');
        return prepare('Lưu bản nháp câu hỏi đang hiển thị; phê duyệt cũ sẽ hết hiệu lực.',async()=>
          await editorControls.current?.save()?succeeded('Đã lưu câu hỏi qua Backend.'):failed('Chưa lưu được câu hỏi. Hãy xem lỗi trong trình chỉnh sửa.'));
      }
      case 'APPROVE_QUESTION': {
        if(!current?.package || current.status!=='complete'||!examService.approveQuestion)return failed('Chưa có câu hỏi hoàn chỉnh để duyệt.');
        const question=resolveQuestion(current,intent.args,editor?.question.stableId);
        if(!question)return failed('Hãy chỉ rõ số câu và phần thi để duyệt.');
        return prepare(`Duyệt câu ${displayNumber(question)} (${question.part??''}) của phiên bản hiện tại.`,async()=>{
          await handleApproveQuestion(question.id);
          return succeeded('Backend đã ghi nhận phê duyệt câu hỏi.');
        });
      }
      case 'EXPORT_ARTIFACT': {
        const kind=intent.args.artifact;
        const format=intent.args.format as 'pdf'|'tex'|'json'|'docx'|'md';
        if(kind==='matrix')return failed('Backend hiện chưa có artifact ma trận xuất riêng. Em chưa tải tệp thay thế.');
        if(kind==='teacher'&&format!=='json')return failed('Đáp án giáo viên hiện chỉ xuất JSON. Em chưa đổi sang bản đề học sinh.');
        if(!current?.package?.approved||current.artifactChanged||editor)return failed('Cần duyệt đúng phiên bản hiện tại trước khi xuất.');
        if(format==='pdf'&&current.preview?.status!=='ready')return failed(previewText(current));
        return prepare(`Tải ${kind==='teacher'?'đáp án giáo viên':'bản đề học sinh'} dạng ${format.toUpperCase()}.`,async()=>
          await exportFile(kind==='teacher'?'TEACHER_KEY':'STUDENT_EXAM',format)?succeeded('Đã yêu cầu trình duyệt tải đúng artifact đã chọn.'):failed('Chưa tải được tệp.'));
      }
      case 'PREPARE_PRACTICE': {
        const topic=matchAdjacentTopic(String(intent.args.topic));
        if(!current||!topic||current.status!=='draft'||editor)return failed('Cần đề nháp và một chủ đề luyện tập lân cận được hỗ trợ.');
        const previous=current.intake?.adjacentTopicId===topic.id?current.intake:undefined;
        const preference=(intent.args.sourcePreference??current.intake?.sourcePreference??'default') as Intake['sourcePreference'];
        const web=preference==='web';
        const count=Number(intent.args.count??previous?.count??topic.defaultCount),minutes=Number(intent.args.minutes??previous?.minutes??topic.defaultMinutes);
        const maxMinutes=web?PRACTICE_LIMITS.researchMinutesMax:PRACTICE_LIMITS.minutesMax;
        const difficulty=typeof intent.args.difficulty==='string'?intent.args.difficulty:current.intake?.difficulty;
        const requirements=typeof intent.args.requirements==='string'?intent.args.requirements:current.intake?.requirements;
        const saveSpec=(validation?:Intake['validation'])=>flushSync(()=>store.setIntake(current.id,{sourceId:messageId,sourceIds:[...new Set([...(current.intake?.sourceIds??[]),messageId])],
          family:'custom',subject:topic.subject,formatId:topic.formatId,version:'1',adjacentTopicId:topic.id,topic:String(intent.args.topic),count,minutes,difficulty,requirements,
          sourcePreference:preference,phase:'collecting',visible:false,validation}));
        if(count<PRACTICE_LIMITS.countMin||count>PRACTICE_LIMITS.countMax||minutes<PRACTICE_LIMITS.minutesMin||minutes>maxMinutes){
          saveSpec('failed');return failed(`Luyện tập hỗ trợ ${PRACTICE_LIMITS.countMin}–${PRACTICE_LIMITS.countMax} câu, ${PRACTICE_LIMITS.minutesMin}–${maxMinutes} phút${web?' khi tìm web':''}. Yêu cầu đang là ${count} câu, ${minutes} phút; chưa tự đổi thông số.`);
        }
        if((current.inputDocuments?.length??0)>PRACTICE_LIMITS.uploadedFilesMax||preference==='attachments'){
          saveSpec('failed');return failed('Backend hiện chưa hỗ trợ tài liệu đính kèm cho luyện SAT/IELTS/TOEIC/TOEFL/ACT. Em chưa đổi nguồn hay đổi sang đề THPT. Có thể dùng cấu trúc tích hợp không tìm mạng hoặc gỡ tài liệu để tìm web.');
        }
        return (async()=>{
          const research=web?await researchAdjacentTopic(current.id,messageId,topic.id,redact(message).slice(0,PRACTICE_LIMITS.researchMessageMax),{count,minutes},activeTurn!.signal):undefined;
          if(!validTurn()||runtimeRef.current!.binding()!==expected)return failed('Cấu hình đã đổi.');
          saveSpec();
          if(intent.args.prepareOnly)return {...succeeded(`Đã lưu cấu hình ${intent.args.topic} · ${count} câu · ${minutes} phút. Chưa chuẩn bị lệnh sinh đề vì yêu cầu không tạo nội dung mới đang có hiệu lực.`),expectedAfter:runtimeRef.current!.binding()};
          const params:ExamRequestParams={formatId:topic.formatId,formatVersion:'1',adjacentTopicId:topic.id,subject:topic.subject as Subject,grade:12,examType:'CUSTOM',
            durationMinutes:minutes,itemCount:count,prompt:[message||`Luyện tập ${topic.label}`,`Chủ đề luyện tập: ${intent.args.topic}`,difficulty?`Độ khó: ${difficulty}`:'',requirements?`Yêu cầu bổ sung: ${requirements}`:''].filter(Boolean).join('\n'),uploadedFiles:[],...(research?{webSources:research.sources}:{})};
          return prepare(`${topic.label} · ${count} câu · ${minutes} phút. ${research?research.searchMode==='live_web'?'Đã tìm nguồn web.':'Tìm web chưa có dữ liệu trực tuyến; dùng cấu trúc tích hợp.':'Không tìm mạng; dùng cấu trúc tích hợp.'} Tạo nội dung mới sẽ dùng AI.`,async()=>{
            const job=await store.generate(current.id,params);
            return job?{status:'accepted',text:'Backend đã nhận yêu cầu luyện tập.'}:failed('Chưa nhận được công việc.');
          },'Tạo đề ngay');
        })();
      }
      case 'PAUSE_GENERATION':
      case 'RESUME_GENERATION':
      case 'RETRY_GENERATION':
      case 'CANCEL_GENERATION': {
        const operation = intent.id === 'PAUSE_GENERATION' ? 'pause' : intent.id === 'RESUME_GENERATION' ? 'resume'
          : intent.id === 'RETRY_GENERATION' ? 'retry' : 'cancel';
        return (async () => {
          await store.loadLibrary();
          if (!validTurn()) return failed('Yêu cầu đã hết hiệu lực.');
          const selection = generationTarget(store.getSnapshot(), current?.id ?? null, operation,
            typeof intent.args.title === 'string' ? intent.args.title : undefined);
          if (!selection.target) return failed(selection.text!);
          const state = await store.generationState(selection.target.id);
          if (!validTurn()) return failed('Yêu cầu đã hết hiệu lực.');
          if (operation === 'cancel') {
            const stopped = await store.stopGeneration(selection.target.id, { jobId: state.jobId, executionVersion: state.executionVersion });
            return stopped?.status === 'cancelled' ? { ...succeeded('Backend xác nhận đã dừng phiên chạy.'), expectedAfter: runtimeRef.current!.binding() }
              : failed('Backend chưa xác nhận việc dừng. Hãy xem trạng thái hiện tại.');
          }
          if(operation==='resume'||operation==='retry')return prepare(`${operation==='resume'?'Tiếp tục':'Thử lại'} phần còn thiếu của “${selection.target.title}”, giữ cùng công việc đã lưu. Thao tác dùng AI.`,async()=>{
            const result=await store.controlGeneration(selection.target!.id,operation,{jobId:state.jobId,executionVersion:state.executionVersion});
            return generationReceipt(operation,result);
          });
          const result = await store.controlGeneration(selection.target.id, operation, { jobId: state.jobId, executionVersion: state.executionVersion });
          return { ...generationReceipt(operation, result), expectedAfter: runtimeRef.current!.binding() };
        })().catch(error => failed(error instanceof Error ? error.message : 'Chưa xác nhận được trạng thái Backend.'));
      }
      case 'RECOVERABLE_JOBS':
        return store.loadLibrary().then(() => {
          const jobs = store.getSnapshot().filter(session => generationJob(session) && (restingGeneration(session.progress?.status) || session.generationStopped));
          return succeeded(jobs.length ? jobs.map(session => `${session.title}: ${statusText(session)}`).join('\n') : 'Chưa có phiên tạm dừng hoặc bị gián đoạn để tiếp tục.');
        });
      case 'OPEN_HISTORY':
        if (!canOpenHistory || !current) return failed('Cần mở đề đã hoàn tất để xem lịch sử phiên bản.');
        flushSync(() => setHistorySession(current.id));
        return succeeded('Đã mở lịch sử phiên bản của đề hiện tại.');
      case 'EXPORT_DOCUMENT': {
        if (!current?.package?.approved || current.artifactChanged || editor) return failed('Cần duyệt phiên bản hiện tại trước khi tải Word hoặc Markdown.');
        const format = intent.args.format as 'docx' | 'md';
        return prepare(`Tải bản đề ${format.toUpperCase()} của phiên bản đã duyệt.`, async () =>
          await exportFile('STUDENT_EXAM', format) ? succeeded('Đã yêu cầu trình duyệt tải tệp.') : failed('Chưa tải được tệp.'));
      }
      case 'OPEN_SETUP':
        if (!current || !['draft', 'error'].includes(current.status) || editor) return failed('Chỉ có thể mở cấu hình cho đề nháp hoặc lần tạo bị lỗi.');
        flushSync(() => { setAgentSelection(undefined); setConfigureId(current.id); setShowQuickModal(true); });
        return presetDialog.current
          ? succeeded('Đã mở phần cấu hình mẫu đề.')
          : failed('Chưa mở được phần cấu hình mẫu đề.');
      case 'HOME':
        flushSync(() => { cancelTransition(); setEditor(null); setShowQuickModal(false); setConfigureId(null); setActiveId(null); setScreen('start'); });
        return succeeded('Đã về màn hình bắt đầu.');
      case 'CREATE_SESSION': {
        const id = store.create('custom');
        flushSync(() => { setAgentSelection(undefined); setShowQuickModal(false); setConfigureId(null); setEditor(null); openSession(id); });
        return succeeded('Đã mở một không gian soạn đề mới.');
      }
      case 'OPEN_SESSION': {
        const title = typeof intent.args.title === 'string' ? fold(intent.args.title) : '';
        if (/^(nay|do|kia)$/.test(title)) return failed('Thầy cô hãy ghi tên của đề muốn mở.');
        if (!title && !/\b(vua tao|vua roi|gan nhat|gan day nhat|moi nhat|hom nay|luc nay|hoi nay|recent|latest)\b/.test(fold(message))) {
          return failed('Thầy cô muốn mở đề nào trong tủ đề?');
        }
        const eligible = store.getSnapshot().filter(item => title || item.id !== current?.id || item.jobId ||
          item.messages.filter(entry => entry.role === 'user').length > 1);
        const matches = title ? searchSessions(eligible, title)
          : eligible.slice().sort((a, b) => b.createdAt.localeCompare(a.createdAt));
        const target = matches[0];
        if (!target) return failed('Chưa tìm thấy đề phù hợp trong tủ đề trên trình duyệt này.');
        if (matches.length > 1 && (title || matches[1].createdAt === target.createdAt)) {
          return failed('Có nhiều đề phù hợp. Thầy cô hãy chọn đúng đề trong tủ đề.');
        }
        flushSync(() => { setShowQuickModal(false); setConfigureId(null); setEditor(null); openSession(target.id); });
        return (async()=>{
          if(target.jobId && target.status==='complete')await store.refresh(target.id);
          if(!validTurn()||activeRef.current!==target.id)return failed('Đề đích đã thay đổi.');
          return {...succeeded(`Đã mở “${target.title}”.`),expectedAfter:runtimeRef.current!.binding()};
        })();
      }
      case 'SET_SIDEBAR':
        if (window.matchMedia('(max-width: 800px)').matches) return failed('Chế độ thu gọn thanh điều hướng chỉ có trên màn hình rộng.');
        flushSync(() => setControlsCollapsed(intent.args.collapsed === true));
        return succeeded(intent.args.collapsed ? 'Đã thu gọn thanh điều hướng.' : 'Đã mở rộng thanh điều hướng.');
      case 'CLOSE_SETUP':
        if (!showQuickModal) return failed('Phần cấu hình đang đóng.');
        flushSync(() => { setShowQuickModal(false); setAgentSelection(undefined); });
        return succeeded('Đã đóng phần cấu hình.');
      case 'LIST_SESSIONS': {
        const title = typeof intent.args.title === 'string' ? fold(intent.args.title) : '';
        const matches = (title ? searchSessions(store.getSnapshot(), title) : store.getSnapshot()).slice(0, 8);
        return succeeded(matches.length ? matches.map(item => `• ${item.title}`).join('\n') : 'Chưa có đề phù hợp trong tủ đề.');
      }
      case 'RENAME': {
        const title = String(intent.args.title);
        if (!current || !fold(message).includes(fold(title))) return failed('Thầy cô hãy ghi rõ tên mới cho cuộc trò chuyện đang mở.');
        return store.rename(current.id, title)
          ? succeeded(`Đã đổi tên cuộc trò chuyện thành “${store.getSnapshot().find(item => item.id === current.id)?.title}”.`)
          : failed('Chưa đặt được tên đã yêu cầu.');
      }
      case 'RECALL': {
        if (!current) return failed('Hãy mở cuộc trò chuyện mà thầy cô muốn xem lại.');
        if (intent.args.what === 'format') {
          const localFormat=()=>{
          if(current.lastParams||current.meta||current.package)return succeeded(`${workspaceDescription(current)}.${current.lastParams?.prompt?`\nYêu cầu trong cấu hình: ${current.lastParams.prompt}`:''}`);
          const source = current.messages.find(item => item.id === current.intake?.sourceId);
          if (!current.intake || !source) return failed('Cuộc trò chuyện này chưa lưu lựa chọn mẫu đề.');
          if (!current.intake.formatId) {
            const family = current.intake.family === 'thpt' ? 'THPT' : current.intake.family === 'vact' ? 'V-ACT' : undefined;
            return succeeded(family ? 'Thầy cô đang xem xét dạng ' + family + '. Chưa chọn mẫu cụ thể.' : 'Thầy cô chưa chọn dạng đề.');
          }
          const label = catalogFormats.find(format=>format.id===current.intake?.formatId)?.displayName??
            (current.intake.adjacentTopicId?matchAdjacentTopic(current.intake.adjacentTopicId)?.label:undefined)??current.intake.subject??'mẫu đã lưu';
          return succeeded(`Mẫu gần nhất là ${label}. Yêu cầu gốc: “${source.content}”.`);
          };
          return readLiveState(current.id).then(state=>state.current?.subject
            ?succeeded(liveStatusText(state.current)+(state.current.requirements?`\nYêu cầu đã gửi: ${state.current.requirements}`:''))
            :localFormat()).catch(()=>failed('Chưa đọc được cấu hình hiện tại từ Backend. Yêu cầu đã lưu vẫn được giữ.'));
        }
        const first = current.messages.find(item => item.id !== messageId && meaningful(item)) ??
          current.messages.find(item => item.id !== messageId && item.role === 'user' &&
            !fastRoute(item.content));
        return first ? succeeded(`Yêu cầu đầu tiên của thầy cô: “${first.content}”`) : failed('Chưa tìm thấy yêu cầu trước đó trong chat này.');
      }
      case 'SET_DRAFT': {
        const value = String(intent.args.text);
        if (!current || !fold(message).includes(fold(value))) return failed('Thầy cô hãy ghi rõ nội dung cần đưa vào ô nhập.');
        store.setDraft(current.id, value);
        return succeeded('Đã đưa nội dung vào ô nhập.');
      }
      case 'CHAT_MESSAGE': {
        if (!current) return failed('Hãy mở cuộc trò chuyện trước.');
        const target = current.messages[Number(intent.args.number) - 1];
        if (!target || target.id === messageId) return failed('Không tìm thấy số tin nhắn này trong cuộc trò chuyện.');
        if (intent.args.operation === 'draft') {
          store.setDraft(current.id, target.content);
          return succeeded('Đã đưa tin nhắn vào ô nhập.');
        }
        if (intent.args.operation === 'copy') {
          if (!navigator.clipboard) return failed('Trình duyệt chưa cho phép sao chép. Thầy cô hãy dùng nút sao chép trên tin nhắn.');
          return navigator.clipboard.writeText(target.content).then(
            () => succeeded('Đã sao chép tin nhắn.'), () => failed('Trình duyệt chưa cho phép truy cập bảng tạm.'),
          );
        }
        if (intent.args.operation === 'branch') {
          return store.branchAtMessage(current.id, target.id).then(id => {
            if (!id) return failed('Chưa tạo được nhánh hội thoại.');
            flushSync(() => { setEditor(null); openSession(id); });
            store.appendMessage(id, 'assistant', 'Đã mở nhánh hội thoại.');
            return succeeded('Đã tạo nhánh hội thoại.');
          }).catch(() => failed('Chưa xác nhận được nhánh hội thoại đã lưu. Hãy tải lại tủ đề.'));
        }
        if (target.role !== 'user') return failed('Chỉ thu hồi được tin nhắn của thầy cô.');
        return prepare('Thu hồi tin nhắn đã chọn và các tin sau. Công việc đã gửi hoặc chỉnh sửa đã lưu vẫn giữ nguyên.', () => {
          store.retractMessage(current.id, target.id);
          return succeeded('Đã thu hồi đoạn hội thoại. Trạng thái công việc trên máy chủ vẫn giữ nguyên.');
        });
      }
      case 'DELETE_SESSION': {
        const name = typeof intent.args.title === 'string' ? fold(intent.args.title) : '';
        const matches = name ? store.getSnapshot().filter(item => fold(item.title) === name) : current ? [current] : [];
        if (matches.length !== 1) return failed('Thầy cô hãy ghi rõ tên của một cuộc trò chuyện trong tủ đề.');
        const target = matches[0];
        if (target.status === 'generating') return failed('Đề đang được tạo. Hiện chưa thể hủy công việc này.');
        return prepare(`Xóa “${target.title}” khỏi tủ đề.`, async () => {
          const latest = store.getSnapshot().find(item => item.id === target.id);
          if (!latest || latest.status === 'generating' || latest.title !== target.title) return failed('Đề đã thay đổi. Hãy kiểm tra lại tủ đề.');
          if (!await store.remove(target.id)) return failed(store.getLibraryError() || 'Chưa xóa được đề khỏi tủ đề.');
          if (current?.id === target.id) flushSync(() => { setEditor(null); setShowQuickModal(false); setConfigureId(null); setActiveId(null); setScreen('start'); });
          return succeeded(`Đã xóa “${target.title}” khỏi tủ đề.`);
        });
      }
      case 'SHOW_FORMATS':
      case 'SELECT_FORMAT':
      case 'FORMAT_DETAILS':
      case 'PREPARE_GENERATION': {
        if (current?.generationStopped && intent.id !== 'SHOW_FORMATS' && intent.id !== 'FORMAT_DETAILS') return failed('Phiên đang giữ kết quả đã lưu. Hãy tiếp tục phiên này hoặc mở workspace mới trước khi lập đề khác.');
        if (intent.id !== 'SHOW_FORMATS' && (!current || !['draft', 'error'].includes(current.status) || editor)) {
          return failed('Đề phải ở trạng thái nháp hoặc lần tạo bị lỗi mới có thể thiết lập.');
        }
        return (async () => {
          try {
            const formats = await getExamFormats();
            if (runtimeRef.current?.binding() !== expected || !validTurn()) {
              return failed('Màn hình đã thay đổi trong lúc tải các mẫu đề.');
            }
            const available = formats.filter(format => format.available);
            const list = available.map(format => `${format.displayName}: ${format.totalQuestions} câu, ${format.durationMinutes} phút`).join('; ');
            if (intent.id === 'SHOW_FORMATS') return succeeded(list || 'Chưa có mẫu đề khả dụng.');
            const selected = intent.args.format ?? agentSelection?.id ?? current?.intake?.formatId;
            if (!selected) return failed(list
              ? `Thầy cô muốn dùng mẫu nào? ${list}. Với Toán THPT, thầy cô có thể nêu thêm chuyên đề.`
              : 'Chưa tải được mẫu đề khả dụng.');
            const format = available.find(item => item.id === selected);
            if (!format || !current) return failed('Mẫu yêu cầu hiện không khả dụng.');
            if (resolved?.formatId === format.id && resolved.version && resolved.version !== format.version) {
              return failed('Mẫu đề đã đổi phiên bản. Thầy cô hãy gửi lại yêu cầu.');
            }
            const family = familyFor(format);
            const named = mentionedFamilies(message);
            if (named.length === 1 && named[0] !== family) return failed('Mẫu được đề xuất khác với dạng đề thầy cô vừa nêu.');
            const compatibility = resolveIntake({ mode: 'structure', family }, message, undefined, formats, messageId);
            if ('text' in compatibility && !compatibility.title) return failed(compatibility.text);
            const intake = { ...resolved, sourceId: messageId, formatId: format.id, version: format.version,
              family, subject: resolved?.subject ?? format.subjects[0] };
            const automaticTitle = family === 'vact' ? 'Soạn đề V-ACT' : 'Đề thi thử ' + format.displayName;
            const expanded = intent.args.details === true || intent.id === 'FORMAT_DETAILS';
            if (intent.id !== 'PREPARE_GENERATION') {
              flushSync(() => {
                store.setIntake(current.id, { ...intake, phase: 'selected' });
                store.suggestTitle(current.id, automaticTitle, messageId, 3);
                setAgentSelection({ formats, id: format.id, expanded });
                setConfigureId(current.id);
                setShowQuickModal(true);
              });
              return { ...succeeded('Đã chọn mẫu. ' + formatOverview(format)), expectedAfter: runtimeRef.current?.binding() };
            }
            const proposal = prepareParams(format, intent.args, message, resolved?.topic);
            if (!proposal.params) return failed(proposal.error);
            const payload = { ...proposal.params, uploadedFiles: (current.inputDocuments ?? []).map(document => document.id) };
            if (current.errorCode === 'network_error' && current.requestSignature &&
                current.requestSignature !== JSON.stringify(payload)) {
              return failed('Lần gửi trước chưa rõ kết quả. Hãy thử lại với thông số cũ trước khi đổi yêu cầu.');
            }
            try {
              await evaluateExamFormat(payload);
            } catch (error) {
              if (runtimeRef.current?.binding() === expected && validTurn()) {
                store.setIntake(current.id, { ...intake, topic: proposal.topic, phase: 'selected', validation: 'failed' });
              }
              return failed(error instanceof Error ? error.message : 'Chưa kiểm tra được chuyên đề theo mẫu đề.');
            }
            if (runtimeRef.current?.binding() !== expected || !validTurn()) {
              return failed('Màn hình đã thay đổi trong lúc kiểm tra mẫu đề.');
            }
            const summary = `${format.displayName} · ${format.totalQuestions} câu · ${format.durationMinutes} phút.${proposal.topic ? ` Chuyên đề: ${proposal.topic}.` : ''} Bấm “Tạo đề thi” để xác nhận gửi yêu cầu.`;
            flushSync(() => {
              store.setIntake(current.id, { ...intake, topic: proposal.topic, phase: 'evaluated', validation: 'passed' });
              store.suggestTitle(current.id, proposal.topic ? 'Đề ôn tập ' + proposal.topic.replace(' và ', ' – ') : automaticTitle,
                messageId, proposal.topic ? 4 : 3);
              setAgentSelection({ formats, id: format.id, expanded: true, summary });
              setConfigureId(current.id);
              setShowQuickModal(true);
            });
            pending.current = {
              workspaceId: current.id,
              binding: runtimeRef.current!.binding(),
              expires: Date.now() + CONFIRMATION_TTL_MS,
              run: async (_sourceId, uploadedFiles) => {
                flushSync(() => { setShowQuickModal(false); setAgentSelection(undefined); });
                store.setIntake(current.id, { ...intake, topic: proposal.topic, phase: 'confirmed', validation: 'passed' });
                const job = await store.generate(current.id, { ...payload, uploadedFiles: uploadedFiles ?? payload.uploadedFiles });
                if (job) return { status: 'accepted', text: 'Máy chủ đã nhận công việc tạo đề. Thầy cô có thể trao đổi tiếp trong khi đợi.' };
                const actual = store.getSnapshot().find(item => item.id === current.id);
                return actual?.errorCode === 'network_error'
                  ? { status: 'unknown', text: 'Chưa rõ máy chủ đã nhận yêu cầu hay chưa. Chỉ thử lại với cùng thông số.' }
                  : failed(actual?.error || 'Chưa nhận được mã công việc tạo đề.');
              },
            };
            return { status: 'pending', text: summary };
          } catch (error) {
            return failed(error instanceof Error ? error.message : 'Chưa kiểm tra được mẫu đề với máy chủ.');
          }
        })();
      }
      case 'STATUS': {
        const all=store.getSnapshot();
        const describe = (facts: Parameters<typeof liveStatusText>[0]) =>
          liveStatusText(facts, intent.args.estimate === true);
        if(current&&!intent.args.name){
          return readLiveState(current.id).then(async state=>{
            if(intent.args.scope==='active'&&state.activeCount)return succeeded(state.active.map(describe).join('\n\n')+(state.activeCount>state.active.length?`\nCòn ${state.activeCount-state.active.length} phiên khác đang chạy.`:''));
            if(state.current)return succeeded((intent.args.scope==='active'?'Hiện không có phiên tạo đề đang chạy.\n':'')+describe(state.current));
            // Legacy/browser-only workspaces may have a job without a server library link.
            if(generationJob(current))return succeeded(statusText({...current,progress:await store.generationState(current.id)}));
            return succeeded(statusText(current));
          }).catch(()=>failed('Chưa đọc được trạng thái mới nhất từ Backend. Đề đã lưu vẫn được giữ.'));
        }
        if(intent.args.scope==='active'){
          const running=all.filter(session=>activeGeneration(session.progress?.status)||(!session.progress?.status&&session.status==='generating'));
          if(!running.length)return succeeded('Hiện không có phiên tạo đề đang chạy.'+(current?`\n${statusText(current)}`:''));
          return Promise.all(running.slice(0,5).map(async session=>{
            try{return statusText({...session,progress:await store.generationState(session.id)});}
            catch{return `${workspaceDescription(session)}: chưa đọc được trạng thái mới nhất từ Backend.`;}
          })).then(lines=>succeeded(lines.join('\n\n')));
        }
        if(current&&!intent.args.name&&!generationJob(current))return succeeded(statusText(current));
        const selection = generationTarget(all, current?.id ?? null, 'status', typeof intent.args.name==='string'?intent.args.name:undefined);
        if (!selection.target) return succeeded(store.getSnapshot().some(session => generationJob(session)) ? selection.text! : current ? statusText(current) : selection.text!);
        const target = selection.target;
        return store.generationState(target.id).then(state => succeeded(statusText({ ...target, progress: state })))
          .catch(() => failed('Chưa đọc được trạng thái mới nhất từ Backend. Kết quả đã lưu vẫn được giữ.'));
      }
      case 'WARNINGS': {
        if (!current?.package) return failed('Chưa có đề hoàn chỉnh để đọc cảnh báo.');
        const pkg = current.package;
        const flagged = current.questions.filter(q => q.answerCheck === 'mismatched')
          .slice(0, 8).map(q => `${q.part || ''} Câu ${displayNumber(q)}`.trim());
        return succeeded(`Cảnh báo nguồn: ${pkg.warnings?.length || 0}. Cảnh báo hình: ${pkg.visualWarnings?.length || 0}. ${flagged.length ? `Câu có đáp án lệch: ${flagged.join(', ')}.` : 'Chưa có cảnh báo lệch đáp án trong dữ liệu hiện tại.'}`);
      }
      case 'SET_VIEW': {
        if (!current?.package || editor || showQuickModal) return failed('Cần đề đã tạo xong và đóng hộp thoại trước khi đổi chế độ xem.');
        const view = intent.args.view as ExamCanvasViewMode;
        flushSync(() => { setAgentOpenedPdf(view === 'pdf'); setViewMode(view); });
        return succeeded(view === 'pdf' ? previewText(current) : view === 'review' ? 'Đã mở chế độ xem đáp án.' : 'Đã mở đề thi.');
      }
      case 'FOCUS_SECTION': {
        if (viewMode === 'pdf' || !current?.package || !canvas.current) return failed('Hãy mở đề thi hoặc chế độ đáp án trước.');
        return canvas.current.section(sectionId(String(intent.args.part))) ? succeeded('Đã cuộn đến phần thi yêu cầu.') : failed('Chưa tìm thấy phần thi trong đề hiện tại.');
      }
      case 'SCROLL_TOP':
        return viewMode !== 'pdf' && canvas.current?.top() ? succeeded('Đã cuộn lên đầu đề.') : failed('Hãy mở trang đề thi trước.');
      case 'FOCUS_QUESTION':
      case 'OPEN_EDITOR':
      case 'PATCH_EDITOR':
      case 'VERIFY_QUESTION':
      case 'REGENERATE_QUESTION': {
        if (!current?.jobId || current.status !== 'complete' || !current.package || showQuickModal) return failed('Chỉ có thể thao tác với câu hỏi trong đề đã tạo xong.');
        const question = resolveQuestion(current, intent.args, editor?.question.stableId);
        if (!question || !question.stableId) return failed('Chưa xác định được câu hỏi. Thầy cô hãy ghi số câu và phần thi hoặc mở câu trong trình chỉnh sửa.');
        const label = `câu ${displayNumber(question)}${question.part ? ` (${question.part})` : ''}`;
        const target = { sessionId: current.id, jobId: current.jobId, question, workspaceId: !current.browserOnly && examService.workspaceLibrary ? current.id : undefined };
        const revision = current.package.revision;
        const remember = () => { if (typeof revision === 'number') flushSync(() => store.rememberQuestion(current.id, question.stableId!, current.jobId!, revision, messageId)); };
        if (intent.id === 'FOCUS_QUESTION') {
          if (editor) return failed('Hãy đóng trình chỉnh sửa trước khi chuyển tới câu hỏi.');
          const view = intent.args.view as ExamCanvasViewMode | undefined;
          if (view || viewMode === 'pdf') flushSync(() => setViewMode(view ?? 'paper'));
          if (!canvas.current?.question(question.stableId)) return failed('Câu hỏi chưa hiển thị trong chế độ hiện tại.');
          remember();
          return succeeded(`Đã chuyển đến ${label}.`);
        }
        if (intent.id === 'PATCH_EDITOR') {
          const field = String(intent.args.field);
          const value = String(intent.args.value);
          if (!fold(message).includes(fold(value)) || redact(value) !== value) {
            return failed('Thầy cô hãy ghi chính xác nội dung muốn điền vào câu hỏi.');
          }
          if (editor && editor.question.stableId !== question.stableId) return failed('Thầy cô hãy hoàn tất câu đang mở trước.');
          if (!editor) flushSync(() => setEditor(target));
          let patched = false;
          flushSync(() => { patched = editorControls.current?.patch(field, value) ?? false; });
          return patched ? succeeded(`Đã điền bản nháp cho ${label}. Thầy cô hãy kiểm tra và bấm nút trong trình chỉnh sửa để tiếp tục.`)
            : failed('Nội dung này không phù hợp với trường của câu hỏi đang mở.');
        }
        if (intent.id === 'OPEN_EDITOR') {
          if (editor && editor.question.stableId !== question.stableId) return failed('Hãy hoàn tất hoặc đóng trình chỉnh sửa đang mở.');
          flushSync(() => setEditor(target));
          remember();
          return succeeded(`Đã mở chỉnh sửa ${label}.`);
        }
        if (intent.id === 'VERIFY_QUESTION' && !examService.verifyQuestion) return failed('Kiểm tra lại đáp án chưa khả dụng trong chế độ hiện tại.');
        const verify = intent.id === 'VERIFY_QUESTION';
        if (!verify && (typeof intent.args.instruction !== 'string' ||
            !fold(message).includes(fold(intent.args.instruction)) || redact(intent.args.instruction) !== intent.args.instruction)) {
          return failed('Thầy cô hãy ghi chính xác yêu cầu muốn dùng để tạo lại câu hỏi.');
        }
        return prepare(verify
          ? `Kiểm tra lại đáp án ${label} bằng bộ giải. Thao tác dùng lượt gọi AI.`
          : `Sinh lại ${label} bằng AI theo yêu cầu “${intent.args.instruction}”.`, async () => {
          try {
            if(!verify && examService.questionRegeneration){
              void startQuestionRun(target,String(intent.args.instruction??'')).catch(()=>{});
              return questionRuns.current.has(current.id)?{status:'accepted',text:`Đã gửi lượt tạo lại ${label}. Có thể hỏi trạng thái hoặc dừng riêng lượt này.`}:{status:'unknown',text:'Chưa xác nhận được lượt tạo lại câu hỏi.'};
            }
            const latest = await editQuestion(target, verify ? 'verify' : 'regen', String(intent.args.instruction ?? ''));
            const result = latest?.questions.find(item => item.stableId === question.stableId);
            if (verify && result?.answerCheck) {
              const verdict = { matched: 'hai đáp án khớp nhau', mismatched: 'hai đáp án khác nhau', needs_recheck: 'vẫn cần kiểm tra' }[result.answerCheck];
              return succeeded(`Kết quả kiểm tra ${label}: ${verdict}.`);
            }
            if (!verify && result && latest?.package?.revision !== current.package?.revision) return succeeded(`Đã cập nhật ${label}. Hãy xem lại phiên bản mới.`);
          } catch {
            return { status: 'unknown', text: 'Chưa xác nhận được kết quả. Hãy kiểm tra phiên bản hiện tại trước khi thử lại.' };
          }
          return { status: 'unknown', text: 'Chưa quan sát được thay đổi trong đề.' };
        });
      }
      case 'CLOSE_EDITOR':
        if (!editor || editorBusy.current.has(editor.sessionId)) return failed('Trình chỉnh sửa chưa mở hoặc đang xử lý.');
        flushSync(() => setEditor(null));
        return succeeded('Đã đóng trình chỉnh sửa.');
      case 'RETRY_PREVIEW':
        if (!current || !['failed', 'unavailable'].includes(current.preview?.status ?? '') || current.artifactChanged) return failed('Chỉ thử lại được khi bản xem trước hiện tại gặp lỗi.');
        return store.requestPreview(current.id, true).then(() => {
          const latest = store.getSnapshot().find(item => item.id === current.id);
          return latest?.preview?.status === 'ready' ? succeeded('Bản xem trước đã sẵn sàng.')
            : ['queued', 'compiling'].includes(latest?.preview?.status ?? '')
              ? { status: 'accepted', text: 'Máy chủ đã nhận yêu cầu dựng lại PDF.' }
              : failed(latest?.previewError || 'Chưa dựng lại được bản xem trước.');
        });
      case 'ADD_NOTE':
      case 'CANCEL_NOTE': {
        if (intent.id === 'ADD_NOTE' && current?.status === 'complete') {
          return dispatch({ id: 'REGENERATE_QUESTION', args: intent.args }, expected, message, messageId);
        }
        if (!current?.jobId) return failed('Chưa có công việc tạo đề để gắn ghi chú.');
        const notes = current.notes ?? [];
        const number = Number(intent.args.number);
        const part = typeof intent.args.part === 'string' ? sectionId(intent.args.part) : undefined;
        const matches = notes.filter(note => note.jobId === current.jobId && note.number === number &&
          (!part || note.part === part) && ['recorded', 'awaiting_review', 'unresolved', 'failed'].includes(note.status));
        if (matches.length > 1) return failed('Có nhiều ghi chú cùng số câu. Thầy cô hãy nêu rõ phần thi.');
        if (intent.id === 'CANCEL_NOTE') {
          if (!matches.length) return failed('Chưa tìm thấy ghi chú của câu này.');
          store.setNotes(current.id, notes.map(note => note.id === matches[0].id ? { ...note, status: 'cancelled' } : note));
          return succeeded(`Đã bỏ ghi chú cho ${noteLabel(matches[0])}.`);
        }
        if (current.status !== 'generating') return failed('Chưa thể ghi chú chỉnh sửa cho công việc hiện tại.');
        const instruction = String(intent.args.instruction);
        if (!fold(message).includes(fold(instruction))) return failed('Thầy cô hãy nêu rõ nội dung muốn chỉnh.');
        if (!matches.length && notes.length >= 32) return failed('Phiên này đã có 32 ghi chú. Thầy cô hãy xử lý các ghi chú trước khi thêm.');
        const note: Note = { id: matches[0]?.id ?? crypto.randomUUID(), sourceId: messageId, jobId: current.jobId,
          number, part: part ?? matches[0]?.part, instruction, status: 'recorded' };
        store.setNotes(current.id, [...notes.filter(item => item.id !== note.id), note]);
        return succeeded(`Đã lưu ghi chú cho ${noteLabel(note)}. Đề đang chạy theo yêu cầu đã gửi.`);
      }
      case 'REVIEW_NOTES':
      case 'APPLY_NOTES': {
        const notes = current?.notes?.filter(note => note.jobId === current.jobId && note.status !== 'cancelled') ?? [];
        if (!notes.length) return failed('Chưa có ghi chú cho công việc hiện tại.');
        const summary = notes.slice(0, 12).map(note => `${noteLabel(note)}: ${note.instruction} (${{
          recorded: 'đã lưu', awaiting_review: 'chờ duyệt', unresolved: 'chưa xác định được câu', applied: 'đã áp dụng',
          failed: 'chưa xác nhận kết quả', cancelled: 'đã hủy',
        }[note.status]})`).join('\n');
        if (intent.id === 'REVIEW_NOTES') return succeeded(summary);
        if (!current?.package || current.status !== 'complete') return failed('Hãy đợi máy chủ tạo xong đề trước khi áp dụng ghi chú.');
        const ready = notes.filter(note => note.status === 'awaiting_review' && note.stableId).slice(0, 4);
        if (!ready.length) return failed('Chưa có ghi chú đã xác định đúng câu và đang chờ duyệt.');
        return prepare(`Áp dụng ${ready.length} ghi chú dưới đây với AI:\n${ready.map(note => `${noteLabel(note)}: ${note.instruction}`).join('\n')}`, async () => {
          const controller = turn.current;
          let revision = current.package?.revision;
          let applied = 0;
          for (const note of ready) {
            const latest = store.getSnapshot().find(session => session.id === current.id);
            const question = latest?.questions.find(item => item.stableId === note.stableId && item.examRevision === revision);
            if (!latest?.jobId || latest.jobId !== current.jobId || latest.package?.revision !== revision ||
                !question || controller?.signal.aborted || activeRef.current !== current.id) break;
            try {
              const after = await editQuestion({ sessionId: latest.id, jobId: latest.jobId, question }, 'regen', note.instruction);
              if (!after?.package || after.package.revision === revision) throw new Error('Chưa nhận được phiên bản mới.');
              revision = after.package.revision;
              store.setNotes(latest.id, (after.notes ?? []).map(item => item.id === note.id
                ? { ...item, status: 'applied', appliedRevision: revision } : item));
              applied++;
            } catch {
              const actual = store.getSnapshot().find(session => session.id === current.id);
              store.setNotes(latest.id, (actual?.notes ?? []).map(item => item.id === note.id ? { ...item, status: 'failed' } : item));
              return { status: 'unknown', text: `Đã áp dụng ${applied} ghi chú. Kết quả cho ${noteLabel(note)} chưa được xác nhận. Các bước sau vẫn chờ.` };
            }
          }
          return applied === ready.length ? succeeded(`Đã áp dụng ${applied} ghi chú. Hãy xem lại phiên bản mới.`)
            : failed(`Đã áp dụng ${applied} ghi chú. Các bước còn lại đang chờ kiểm tra.`);
        });
      }
      case 'APPROVE':
        if (!current || editor || !store.canApprove(current.id)) return failed('Thầy cô hãy tự mở và kiểm tra PDF của phiên bản hiện tại trước khi phê duyệt.');
        return prepare(`Phê duyệt phiên bản ${current.package?.revision}. Hãy xác nhận sau khi đã xem kỹ PDF và các cảnh báo.`, async () =>
          await approve() ? succeeded('Đã phê duyệt phiên bản hiện tại.') : failed('Chưa xác nhận được phê duyệt. Hãy kiểm tra trạng thái của đề.'));
      case 'EXPORT': {
        if(intent.args.format==='json')return failed('Thầy cô muốn JSON bản đề học sinh hay đáp án giáo viên? Hãy chỉ rõ artifact cần tải.');
        const format = intent.args.format as 'pdf' | 'tex' | 'json';
        if (!current?.package?.approved || current.artifactChanged || editor) return failed('Phiên bản hiện tại cần được phê duyệt trước khi tải tệp.');
        if (format === 'pdf' && (current.preview?.status !== 'ready' || current.preview.revision !== current.package.revision ||
            current.preview.contentHash !== current.package.contentHash)) return failed('Bản PDF của phiên bản hiện tại chưa sẵn sàng.');
        return prepare(`Tải tệp ${format.toUpperCase()} của phiên bản ${current.package.revision}.`, async () =>
          await exportFile(format === 'json' ? 'TEACHER_KEY' : 'STUDENT_EXAM', format)
            ? succeeded('Đã yêu cầu trình duyệt tải tệp.') : failed('Chưa tải được tệp.'));
      }
      default: return failed('Thao tác này chưa có liên kết với màn hình hiện tại.');
    }
  };
  useLayoutEffect(() => {
    activeRef.current = activeId;
    runtimeRef.current = {
      binding,
      dispatch: (intent, expected, message, source, intake) => binding() === expected ? dispatch(intent, expected, message, source, intake)
        : { status: 'failed', text: 'Trạng thái đã thay đổi. Thầy cô hãy gửi lại yêu cầu.' },
    };
  });

  const sidebarLabel = controlsCollapsed ? 'Mở rộng thanh điều hướng' : 'Thu gọn thanh điều hướng';

  if (showWelcome) return <AstraWelcome onComplete={finishWelcome} />;

  return (
    <div className={`app-shell create-mode workspace-active integrated-shell ${revealingWorkspace ? 'workspace-revealing' : ''} ${controlsCollapsed ? 'controls-collapsed' : ''}`}>
      <header className="app-header">
        <div className="sidebar-brand-row">
          <button type="button" className="app-brand" aria-label="ASTRA — Về màn hình bắt đầu" title="Về màn hình bắt đầu" onClick={newExam}>
            <span className="brand-emblem"><AstraLogo className="app-brand-logo" /></span>
            <span className="brand-wordmark">ASTRA</span>
          </button>
          <button type="button" className="sidebar-collapse-btn" onClick={() => setControlsCollapsed(value => !value)} aria-label={sidebarLabel} aria-expanded={!controlsCollapsed} title={sidebarLabel}>
            {controlsCollapsed ? <PanelLeftOpen size={16} aria-hidden="true" /> : <PanelLeftClose size={16} aria-hidden="true" />}
          </button>
        </div>
        <SidebarExamLibrary sessions={sessions} activeId={screen === 'workspace' ? activeId : null}
          error={libraryError} onRetry={store.retryLibrary} onNew={newExam} onOpen={openManually}
          collapsed={controlsCollapsed} searchSaved={examService.workspaceLibrary?.search}
          browserImport={browserImport} onImport={store.importBrowserLibrary}
          onDelete={async id => {
            if (await store.remove(id) && configureId === id) { setConfigureId(null); setShowQuickModal(false); }
          }} />
        <button className="side-rail-edge" type="button" onClick={() => setControlsCollapsed(value => !value)} aria-label={sidebarLabel} aria-expanded={!controlsCollapsed} title={sidebarLabel} />
        <div className="header-right"><ConnectionSetup busy={chatPending || active?.status === 'generating' || Boolean(questionPending)} /><span className="header-avatar" aria-label="Người dùng: Cùng thầy cô" title="Cùng thầy cô">GV</span><span className="header-session">Cùng thầy cô</span></div>
      </header>

      {store.storageWarning && <div className="canvas-alert-banner is-error" role="alert">{store.storageWarning}</div>}
      {admissionError && <div className="canvas-alert-banner is-error" role="alert">{admissionError}</div>}
      {/* Main content */}
      {screen === 'start' && <WorkspaceStart documents={landingDocuments} onDocumentsChange={setLandingDocuments} exiting={leavingStart} draft={landingDraft} onDraftChange={setLandingDraft} onTemplate={() => { setConfigureId(null); setAgentSelection(undefined); setShowQuickModal(true); }} onDetailed={handleDetailedStart} onSend={handleLandingSend} />}

      {screen === 'workspace' && active && (
        <WorkspaceLayout key={active.id}>
          {{
            left: (
              <>
                <div className="studio-chat-heading"><div><span className="studio-kicker">KHÔNG GIAN SOẠN ĐỀ</span><h2>Cùng soạn đề</h2></div></div>
                <div className="session-context"><strong>{active.mode === 'template' ? active.meta?.title ?? active.title : active.title}</strong></div>
                {(!active.generationId && !active.generationStopped && active.status === 'draft' && !chatDrafts[active.id]) && <div className="session-create-action">
                  <button type="button" className="button-primary" onClick={() => { cancelTurn(); setAgentSelection(undefined); setConfigureFormatId(active.intake?.formatId); setConfigureId(active.id); setShowQuickModal(true); }}>Tạo đề từ yêu cầu</button>
                </div>}
                {undoConflict?.id === active.id && <div className="editor-error-box" role="alert">
                  <strong>Có xung đột khi hoàn tác. Hãy kiểm tra câu hỏi và ngữ liệu chung.</strong>
                  <details open><summary>So sánh đề bài</summary>
                    <div>Hiện tại: <MathRenderer content={undoConflict.current} /></div>
                    <div>Sau thay đổi: <MathRenderer content={undoConflict.afterChange} /></div>
                    <div>Trước thay đổi: <MathRenderer content={undoConflict.beforeChange} /></div>
                  </details>
                  <button type="button" className="button-secondary" onClick={() => setUndoConflict(undefined)}>Đóng</button>
                </div>}
                <ChatHistory messages={messages} onSuggestion={value => store.setDraft(active.id, value)} onEditMessage={message => store.setDraft(active.id, message.content)} onRetractMessage={message => { cancelTurn(); store.retractMessage(active.id, message.id); }} onBranchMessage={message => { cancelTurn(); void branchFromMessage(active.id, message); }}
                  currentJobId={active.jobId} undoing={undoing} onUndoChange={sharedId && active.package?.revision ? message => void undoRecordedChange(message) : undefined} />
                {(chatDrafts[active.id] || pendingActionMeta?.workspaceId === active.id) && (
                  <ChatConfigCard
                    draft={chatDrafts[active.id]}
                    formats={catalogFormats}
                    disabled={chatPending || isGenerating}
                    pendingAction={pendingActionMeta?.workspaceId === active.id && pending.current?.workspaceId === active.id ? {
                      label: pendingActionMeta.label,
                      confirmLabel: pendingActionMeta.confirmLabel,
                      onConfirm: () => {
                        void confirmPending()
                          .then(effect => store.appendMessage(active.id, 'assistant', effect.text));
                      },
                      onCancel: () => {
                        setPendingConfirmation(null);
                        store.appendMessage(active.id, 'assistant', 'Đã hủy thao tác đang chờ.');
                      },
                    } : null}
                    onChange={patch => {
                      setPendingConfirmation(null);
                      if(active.intake)store.setIntake(active.id,patchSpec(active.intake,patch,catalogFormats));
                    }}
                    onGenerate={() => {
                      const currentDraft = chatDrafts[active.id];
                      if (!currentDraft) return;
                      const {params,error:problem} = paramsForSpec(active.intake,catalogFormats,active.inputDocuments??[]);
                      if (!params) {store.appendMessage(active.id,'assistant',problem??'Cấu hình chưa hợp lệ.');return;}
                      setPendingConfirmation(null);
                      void store.generate(active.id, params);
                    }}
                    onOpenModal={() => {
                      const fmtId = chatDrafts[active.id]?.formatId;
                      setConfigureFormatId(fmtId);
                      setConfigureId(active.id);
                      setAgentSelection(undefined);
                      setShowQuickModal(true);
                    }}
                    onDismiss={() => {setPendingConfirmation(null);if(active.intake)store.setIntake(active.id,{...active.intake,visible:false});}}
                  />
                )}
              </>
            ),
            right: (
              <>
                {hasValidExam && (active.error || active.generationError) && (
                  <div className="canvas-alert-banner is-error" role="alert">
                    <AlertCircle size={17} aria-hidden="true" />
                    <span className="canvas-alert-copy">{active.error || active.generationError}</span>
                    {active.lastParams && (
                      <button
                        type="button"
                        className="button-secondary canvas-alert-retry"
                        onClick={() => void store.generate(active.id, active.lastParams!)}
                      >
                        <RefreshCw size={13} aria-hidden="true" />
                        <span>Thử lại</span>
                      </button>
                    )}
                  </div>
                )}
                {!hasValidExam && active.status === 'error' && !isGenerating && (
                  <section className="canvas-error-recovery" role="alert" aria-label="Khôi phục lỗi tạo đề">
                    <div className="canvas-error-recovery-head">
                      <AlertCircle size={18} aria-hidden="true" />
                      <div>
                        <strong>Chưa tạo được đề thi hợp lệ</strong>
                        <p>{active.error || active.generationError || 'Quá trình tạo đề bị gián đoạn hoặc gặp lỗi định dạng.'}</p>
                      </div>
                    </div>
                    {(active.lastParams || active.meta || (active.inputDocuments?.length ?? 0) > 0) && (
                      <div className="canvas-error-recovery-meta">
                        <span>
                          Cấu hình đã giữ: {active.lastParams?.subject || active.meta?.subject || active.title}
                          {active.lastParams ? ` · ${active.lastParams.itemCount} câu · ${active.lastParams.durationMinutes} phút`
                            : active.meta ? ` · ${active.meta.totalCount} câu · ${active.meta.duration} phút` : ''}
                          {(active.inputDocuments?.length ?? 0) > 0 ? ` · ${active.inputDocuments!.length} tệp đính kèm` : ''}
                        </span>
                      </div>
                    )}
                    <div className="canvas-error-recovery-actions">
                      <button
                        type="button"
                        className="button-primary"
                        onClick={() => {
                          cancelTurn();
                          if (active.lastParams) {
                            void store.generate(active.id, active.lastParams);
                            return;
                          }
                          const matched = catalogFormats.find(f =>
                            f.available && (f.id === active.intake?.formatId || f.subjects.some(s => s === active.meta?.subject))
                          );
                          setAgentSelection(undefined);
                          setConfigureFormatId(matched?.id ?? active.intake?.formatId);
                          setConfigureId(active.id);
                          setShowQuickModal(true);
                        }}
                      >
                        <RefreshCw size={14} aria-hidden="true" />
                        <span>Thử tạo lại</span>
                      </button>
                      <button
                        type="button"
                        className="button-secondary"
                        onClick={() => {
                          cancelTurn();
                          const matched = catalogFormats.find(f =>
                            f.available && (f.id === active.lastParams?.formatId || f.id === active.intake?.formatId || f.subjects.some(s => s === active.meta?.subject))
                          );
                          setAgentSelection(undefined);
                          setConfigureFormatId(matched?.id);
                          setConfigureId(active.id);
                          setShowQuickModal(true);
                        }}
                      >
                        <Settings2 size={14} aria-hidden="true" />
                        <span>Chỉnh cấu hình</span>
                      </button>
                    </div>
                  </section>
                )}
                {(questionStage || ((isGenerating || active.generationId) && active.progress)) && (
                  <div className="canvas-progress-banner" role="status" aria-live="polite">
                    <div className="canvas-progress-top">
                      <span className="canvas-progress-label">
                        <LoaderCircle className="exam-status-spinner" size={15} aria-hidden="true" />
                        <span>{questionPending && questionStage
                          ? `${questionStage[1]} · Câu ${displayNumber(questionPending.target.question)}`
                          : formatProgressStatus(active.progress?.statusMessage || '')}</span>
                      </span>
                      <strong className="canvas-progress-pct">{questionStage?.[0] ?? active.progress?.percent}%</strong>
                    </div>
                    <div className="canvas-progress-controls">
                      <div className="canvas-progress-track" aria-hidden="true">
                        <div className="canvas-progress-fill" style={{ width: `${Math.max(4, Math.min(100, questionStage?.[0] ?? active.progress?.percent ?? 0))}%` }} />
                      </div>
                      {questionPending ? (
                        <button type="button" className="button-secondary canvas-stop-generation"
                          disabled={questionPending.stopping || !questionPending.receipt}
                          onClick={() => void stopQuestionRun(active.id)}>
                          {questionPending.stopping ? 'Đang dừng…' : 'Dừng'}
                        </button>
                      ) : examService.stopGeneration && (active.generationId || active.jobId) && (
                        <>
                        {examService.pauseGeneration && <button type="button" className="button-secondary canvas-stop-generation"
                          disabled={active.stoppingGeneration || active.continuingGeneration || active.progress?.status === 'pausing'}
                          onClick={() => void store.pauseGeneration(active.id)}>
                          {active.progress?.status === 'pausing' ? 'Đang lưu để tạm dừng…' : 'Tạm dừng'}
                        </button>}
                        <button type="button" className="button-secondary canvas-stop-generation"
                          disabled={active.stoppingGeneration || active.continuingGeneration}
                          onClick={() => void store.stopGeneration(active.id)}>
                          {active.stoppingGeneration ? 'Đang dừng…' : 'Dừng'}
                        </button>
                        </>
                      )}
                    </div>
                  </div>
                )}
                {questionRun?.receipt?.status === 'cancelled' && !isGenerating && !active.generationId && (
                  <div className="canvas-progress-banner canvas-progress-controls">
                    <span className="canvas-progress-label" role="status">Đã dừng tạo lại câu {displayNumber(questionRun.target.question)}</span>
                  </div>
                )}
                {active.generationStopped && (
                  <div className="canvas-progress-banner canvas-progress-controls">
                    <span className="canvas-progress-label" role="status">
                      {active.progress?.statusMessage || 'Đã dừng'}
                      {active.progress && ` · Đã lưu ${active.progress.completedItems}/${active.progress.totalItems} câu`}
                    </span>
                    {examService.resumeGeneration && active.stoppedJobId && (
                      <button type="button" className="button-secondary canvas-stop-generation"
                        disabled={active.continuingGeneration || active.progress?.resumeAvailable === false}
                        onClick={() => void (active.progress?.error ? store.retryGeneration(active.id) : store.continueGeneration(active.id))}>
                        {active.continuingGeneration ? 'Đang yêu cầu tiếp tục…' : active.progress?.error ? 'Thử lại phần còn thiếu' : 'Tiếp tục'}
                      </button>
                    )}
                  </div>
                )}
                {!!active.package?.warnings?.length && (
                  <details className="canvas-source-warnings">
                    <summary>
                      <AlertTriangle size={14} aria-hidden="true" />
                      <span>Cảnh báo cần kiểm tra ({active.package.warnings.length})</span>
                    </summary>
                    <div className="canvas-source-warnings-body">
                      {active.package.warnings.map((warning, i) => (
                        <p key={i}>{warning.questionId && <strong>{warning.questionId} · </strong>}{warning.message}</p>
                      ))}
                    </div>
                  </details>
                )}
                {!!active.package?.visualWarnings?.length && (
                  <div className="pdf-preview-warning" role="alert">
                    <strong>Cảnh báo hình vẽ / bảng biểu ({active.package.visualWarnings.length})</strong>
                    <p>Đề thi chưa tự sinh hình vẽ còn thiếu. Thầy cô hãy sửa câu hỏi bị ảnh hưởng.</p>
                    {active.package.visualWarnings.map((warning, i) => {
                      const target = active.questions.find(q => q.stableId === warning.questionId);
                      const label = target ? `Câu ${target.id}` : warning.questionId;
                      return (
                        <p key={`${warning.questionId}-${i}`}>
                          <strong>{label}:</strong> {formatVisualWarning(warning.code)}
                        </p>
                      );
                    })}
                  </div>
                )}
                <ExamPaperView
                  header={<CanvasHeader
                    examMeta={examMeta}
                    isGenerating={isGenerating}
                    canExport={active.package?.approved === true && !active.artifactChanged}
                    showApprove={active.status === 'complete' && !active.package?.approved && !active.artifactChanged}
                    canApprove={store.canApprove(active.id)}
                    approving={approving}
                    onOpenPdfPreview={openPdfManually}
                    onApprove={() => { void approve(); }}
                    onShowHistory={canOpenHistory ? () => setHistorySession(active.id) : undefined}
                    onUndoRegeneration={latestUndo ? () => void undoRecordedChange(latestUndo)
                      : canUndo ? () => void undoRegeneration() : undefined}
                    undoing={undoing}
                  />}
                  controlsRef={canvas}
                  onManualPdfOpen={() => store.markPreviewOpened(active.id)}
                  onExport={format => exportFile(format === 'json' ? 'TEACHER_KEY' : 'STUDENT_EXAM', format)}
                  questions={liveQuestions}
                  passages={active.package?.passages}
                  examMeta={examMeta}
                  isGenerating={isGenerating}
                  progressMessage={isGenerating && active.progress?.statusMessage ? formatProgressStatus(active.progress.statusMessage) : undefined}
                  latestQuestionCount={prevQuestionCount}
                  viewMode={viewMode}
                  onViewModeChange={mode => { setAgentOpenedPdf(false); setViewMode(mode); }}
                  examId={active.jobId || active.package?.examId}
                  revision={active.package?.revision}
                  contentHash={active.package?.contentHash}
                  approved={active.package?.approved}
                  preview={active.preview}
                  warnings={active.package?.warnings}
                  visualWarnings={active.package?.visualWarnings}
                  previewLog={active.previewLog}
                  previewError={active.previewError}
                  previewErrorCode={active.previewErrorCode}
                  artifactChanged={active.artifactChanged}
                  onRetryPreview={handleRetryPreview}
                  onPreviewOpened={handlePreviewOpened}
                  verifyingQuestionId={verifyingQuestionId}
                  approvingQuestionId={approvingQuestionId}
                  onVerifyQuestion={examService.verifyQuestion && active.jobId && active.package?.revision !== undefined && !isGenerating ? id => { void handleVerifyQuestion(id); } : undefined}
                  onApproveQuestion={examService.approveQuestion && active.jobId && active.package?.revision !== undefined && !isGenerating ? (id, reason) => handleApproveQuestion(id, reason) : undefined}
                  onEditQuestion={id => {
                    const question = active.questions.find(item => item.id === id);
                    if (active.jobId && question) setEditor({
                      sessionId: active.id, jobId: active.jobId, question, workspaceId: sharedId ?? undefined,
                    });
                  }}
                />
              </>
            ),
            composer: <ModernChatBar compact documents={active.inputDocuments ?? []} onDocumentsChange={documents => store.setInputDocuments(active.id, documents)} onSend={handleSendMessage} disabled={chatPending} draft={active.draft} onDraftChange={value => store.setDraft(active.id, value)} />,
          }}
        </WorkspaceLayout>
      )}

      {/* Quick preset modal */}
      {showQuickModal && (
        <QuickPresetModal
          documents={configureId ? sessions.find(session => session.id === configureId)?.inputDocuments ?? [] : landingDocuments}
          onDocumentsChange={documents => { if (configureId) store.setInputDocuments(configureId, documents); else setLandingDocuments(documents); }}
          title={configureId ? 'Thiết lập đề theo yêu cầu' : 'Tạo đề từ mẫu'}
          onDialogMount={node => { presetDialog.current = node; }}
          agentSelection={agentSelection}
          initialFormatId={configureFormatId}
          spec={sessions.find(session=>session.id===configureId)?.intake}
          onManualSelect={() => { setPendingConfirmation(null); setAgentSelection(undefined); }}
          onStart={handleQuickStart}
          onClose={closeQuickModal}
        />
      )}
      {history && active?.jobId && active.package?.revision && historySession === active.id && (
        <ExamVersionHistory key={active.jobId} history={history} jobId={active.jobId} revision={active.package.revision}
          workspaceId={active.browserOnly ? undefined : active.id}
          onClose={() => setHistorySession(null)} onRestore={async (version, revision, jobId, targetJobId) => {
            await restoreVersion(active.id, jobId, version, revision, active.browserOnly ? undefined : active.id, targetJobId);
            setHistorySession(null);
          }} />
      )}
      {editor && <QuestionEditor controlsRef={editorControls} question={editor.question} onClose={() => setEditor(null)}
        onVerify={examService.verifyQuestion && editor.question.examRevision !== undefined ? async () => {
          await editQuestion(editor, 'verify');
          if (activeRef.current === editor.sessionId) setViewMode('review');
        } : undefined}
        onSave={async question => { await editQuestion(editor, 'save', question); }}
        onRegenerate={async instruction => { await startQuestionRun(editor, instruction); }}
      />}
    </div>
  );
};

export default App;
