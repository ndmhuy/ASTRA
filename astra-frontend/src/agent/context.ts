import type { UiContextSnapshot } from './contracts';

export type UnversionedUiContext = Omit<UiContextSnapshot, 'stateVersion'>;

function stableFingerprint(context: UnversionedUiContext): string {
  return JSON.stringify(context);
}

export class UiContextTracker {
  private version = 0;
  private fingerprint = '';

  capture(context: UnversionedUiContext): UiContextSnapshot {
    const next = stableFingerprint(context);
    if (next !== this.fingerprint) {
      this.fingerprint = next;
      this.version += 1;
    }
    return { ...context, stateVersion: Math.max(1, this.version) };
  }
}
