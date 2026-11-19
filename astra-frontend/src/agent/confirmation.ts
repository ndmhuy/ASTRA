import type { PendingAgentConfirmation, UiContextSnapshot } from './contracts';

export function stableValue(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableValue).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.entries(value).sort(([a],[b]) => a.localeCompare(b)).map(([k,v]) => `${JSON.stringify(k)}:${stableValue(v)}`).join(',')}}`;
  return JSON.stringify(value) ?? 'null';
}

export function confirmationBinding(context: UiContextSnapshot, kind: PendingAgentConfirmation['kind']): string {
  return stableValue({ workspace: context.workspaceId, exam: context.examId, revision: context.examRevision, hash: context.contentHash,
    ...(kind === 'generation' ? { format: context.setup.selectedFormatId, prompt: context.setup.prompt, formats: context.setup.formats } : {}),
    ...(kind === 'ui_action' ? { editor: context.editorDraft } : {}),
    ...(kind === 'revision' ? { notes: context.notes } : {}),
  });
}

export function confirmationValid(context: UiContextSnapshot): boolean {
  const pending = context.pendingConfirmation;
  return Boolean(pending && pending.workspaceId === context.workspaceId
    && Date.now() - Date.parse(pending.createdAt) >= 0
    && Date.now() - Date.parse(pending.createdAt) < 10 * 60_000
    && pending.binding === confirmationBinding(context, pending.kind));
}

// Progress percentages, assistant messages and task bookkeeping cannot change an
// action target. Job identity, exam revision, drafts and navigation can.
export function actionScope(context: UiContextSnapshot): string {
  const { activeTask: _task, stateVersion: _version, messages: _messages, capabilities: _caps, activeJob, ...state } = context;
  return stableValue({ ...state, activeJob: activeJob?.id || null });
}
