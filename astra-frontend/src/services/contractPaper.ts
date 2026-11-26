import type { ExamPackage, ExamPassage, QuestionChoices } from '../types/exam';

type Letter = keyof QuestionChoices;
type StatementLetter = 'a' | 'b' | 'c' | 'd';
type Run =
  | { type: 'text'; text: string }
  | { type: 'math'; latex: string }
  | { type: 'chem'; notation: string }
  | { type: 'line_break' }
  | { type: 'blank' | 'marker'; label: string };
type Block = { type: 'paragraph'; runs: Run[] } | { type: 'figure'; assetId: string; alt: string };
type BaseItem = { id: string; stem: Block[]; passageIds: string[]; number: number };
type Item = BaseItem & (
  | { type: 'mcq'; choices: Record<Letter, Run[]> }
  | { type: 'true_false'; statements: Record<StatementLetter, Run[]> }
  | { type: 'short_answer'; responseKind: 'numeric' | 'digit_sequence' }
);

export interface StudentPaper {
  schemaVersion: 'astra-thpt-paper-v1';
  examId: string;
  revision: number;
  contentHash: string;
  sections: { id: 'P1' | 'P2' | 'P3'; items: Item[] }[];
  passages: {
    id: string;
    sectionId: ExamPassage['section'];
    kind: 'reading' | 'cloze' | 'ordering' | 'context' | 'data_set';
    questionRange: [number, number];
    instructions: Run[];
    blocks: Block[];
  }[];
  assets: { id: string; mimeType: string }[];
}

function runsText(runs: Run[]): string {
  return runs.map(run => {
    switch (run.type) {
      case 'text': return run.text;
      case 'math': return '$' + run.latex + '$';
      case 'chem': return '$\\mathrm{' + run.notation + '}$';
      case 'line_break': return '\n';
      case 'blank': return '(' + run.label + ') ____';
      case 'marker': return '[' + run.label + ']';
    }
  }).join('');
}

function blockText(blocks: Block[]): string {
  return blocks.filter(block => block.type === 'paragraph').map(block => runsText(block.runs)).join('\n\n');
}

export function adaptStudentPaper(pkg: ExamPackage, apiBase: string): ExamPackage {
  const paper = pkg.studentPaper;
  if (!paper) return pkg;
  if (paper.schemaVersion !== 'astra-thpt-paper-v1' || paper.examId !== 'exam-' + pkg.examId ||
      paper.revision !== pkg.revision || paper.contentHash !== pkg.contentHash) {
    throw new Error('Bản đề JSON không khớp với phiên bản hiện tại.');
  }
  const legacy = new Map(pkg.questions.map(question => [question.stableId?.toLowerCase(), question]));
  const questions = paper.sections.flatMap(section => section.items.map(item => {
    const prior = legacy.get(item.id);
    if (!prior || item.type !== prior.questionType) {
      throw new Error('Câu hỏi trong bản đề JSON không khớp với dữ liệu giáo viên.');
    }
    legacy.delete(item.id);
    const figures = item.stem.filter(block => block.type === 'figure').map(block => {
      const asset = paper.assets.find(entry => entry.id === block.assetId);
      if (!asset) throw new Error('Thiếu hình minh họa trong bản đề JSON.');
      return {
        url: apiBase + '/exams/' + encodeURIComponent(pkg.examId) + '/assets/' + encodeURIComponent(asset.id),
        mimeType: asset.mimeType,
        alt: block.alt,
      };
    });
    const common = {
      ...prior, part: section.id, stem: blockText(item.stem) || prior.stem, figures,
      passageId: item.passageIds[0] ?? null, groupInstruction: undefined,
    };
    switch (item.type) {
      case 'mcq':
        return {
          ...common,
          choices: {
            A: runsText(item.choices.A), B: runsText(item.choices.B),
            C: runsText(item.choices.C), D: runsText(item.choices.D),
          },
        };
      case 'true_false':
        return {
          ...common,
          statements: (['a', 'b', 'c', 'd'] as const).map((letter, index) => {
            const statement = prior.statements?.[index];
            if (!statement) throw new Error('Thiếu đáp án giáo viên cho câu đúng/sai.');
            return { ...statement, text: runsText(item.statements[letter]) };
          }),
        };
      case 'short_answer':
        return { ...common, responseKind: item.responseKind };
    }
  }));
  if (legacy.size) throw new Error('Bản đề JSON thiếu câu hỏi.');
  const passages: ExamPassage[] = paper.passages.map(passage => ({
    id: passage.id, section: passage.sectionId,
    questionRange: passage.questionRange, instruction: runsText(passage.instructions),
    kind: passage.kind === 'data_set' ? 'data_set' : 'passage',
    text: blockText(passage.blocks),
  }));
  return { ...pkg, questions, passages };
}
