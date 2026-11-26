/**
 * ASTRA - Service Layer & Backend Abstraction
 * 
 * Provides an abstract service interface (IExamService) that completely decouples
 * the Front-End UI from backend implementation choices (FastAPI, Flask, Next.js, SSE, or WebSockets).
 * 
 * Includes:
 * 1. MockExamService: High-fidelity simulation for offline testing, UI demonstration, and verification loops.
 * 2. ApiExamService: Production adapter ready to wire to real backend endpoints.
 */

import type {
  ExamPackage,
  ExamPreviewState,
  ExamRequestParams,
  GenerationProgress,
  QuestionItem
} from '../types/exam';
import type { ExamFormat, ExportFormat } from '../types/exam';
import { humanizeErrorMessage } from '../utils/userMessages.ts';
import { adaptStudentPaper } from './contractPaper.ts';

export interface IExamService {
  startGeneration(params: ExamRequestParams): Promise<{ jobId: string }>;
  onProgress(jobId: string, callback: (progress: GenerationProgress) => void): () => void;
  getExamPackage(jobId: string): Promise<ExamPackage>;
  regenerateQuestion(jobId: string, questionId: number, instruction?: string, revision?: number): Promise<QuestionItem>;
  updateQuestion(jobId: string, updatedQuestion: QuestionItem): Promise<void>;
  verifyQuestion?(jobId: string, questionId: number, revision: number): Promise<void>;
  downloadExport(jobId: string, type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: ExportFormat): Promise<void>;
  approveExam?(jobId: string, pkg: ExamPackage): Promise<ExamPackage>;
  requestPreview?(jobId: string, binding: { revision: number; contentHash: string }): Promise<ExamPreviewState>;
  getPreviewStatus?(jobId: string, binding: { revision: number; contentHash: string }, statusUrl?: string): Promise<ExamPreviewState>;
  getPreviewLog?(logUrl: string): Promise<string>;
}

// ============================================================================
// REALISTIC SAMPLE EXAM DATA (VẬT LÝ 12 - TỐT NGHIỆP THPT)
// Includes standard LaTeX formulas and multi-agent audit notes.
// ============================================================================
const INITIAL_MOCK_QUESTIONS: QuestionItem[] = [
  {
    id: 1,
    topic: 'Dao động cơ',
    level: 'NHAN_BIET',
    stem: 'Một vật dao động điều hòa theo phương trình $x = A\\cos(\\omega t + \\varphi)$. Đại lượng $\\omega$ được gọi là gì của dao động?',
    choices: {
      A: 'Pha ban đầu',
      B: 'Tần số góc',
      C: 'Biên độ dao động',
      D: 'Chu kỳ dao động'
    },
    key: 'B',
    explanation: 'Trong phương trình dao động điều hòa $x = A\\cos(\\omega t + \\varphi)$, đại lượng $\\omega$ (đơn vị rad/s) là tần số góc của dao động.',
    sourceReference: 'SGK Vật lý 12 - Kết Nối Tri Thức, Bài 1 (Trang 6)',
    status: 'VERIFIED',
    writerKey: 'B',
    solverKey: 'B',
    revisionCount: 0,
    auditNotes: 'Blind Solver và Writer đồng thuận chọn B. Khái niệm cơ bản chính xác theo SGK.'
  },
  {
    id: 2,
    topic: 'Dao động cơ',
    level: 'THONG_HIEU',
    stem: 'Một con lắc lò xo gồm lò xo có độ cứng $k = 100\\text{ N/m}$ và vật nhỏ khối lượng $m = 250\\text{ g}$. Chu kỳ dao động riêng của con lắc là:',
    choices: {
      A: '$0{,}1\\pi\\text{ s}$',
      B: '$0{,}2\\pi\\text{ s}$',
      C: '$0{,}4\\pi\\text{ s}$',
      D: '$0{,}5\\pi\\text{ s}$'
    },
    key: 'A',
    explanation: 'Áp dụng công thức chu kỳ con lắc lò xo: $T = 2\\pi \\sqrt{\\frac{m}{k}} = 2\\pi \\sqrt{\\frac{0{,}25}{100}} = 2\\pi \\cdot \\frac{0{,}5}{10} = 0{,}1\\pi\\text{ s}$.',
    sourceReference: 'SGK Vật lý 12 - Chương 1: Dao động điều hòa',
    status: 'VERIFIED',
    writerKey: 'A',
    solverKey: 'A',
    revisionCount: 0,
    auditNotes: 'Kiểm tra công thức và phép tính số học: Cả hai bên tính chính xác $T = 0{,}1\\pi\\text{ s}$.'
  },
  {
    id: 3,
    topic: 'Sóng cơ & Sóng âm',
    level: 'VAN_DUNG',
    stem: 'Trên một sợi dây đàn hồi dài $1{,}2\\text{ m}$ hai đầu cố định, đang có sóng dừng với 3 bụng sóng. Biết tốc độ truyền sóng trên dây là $v = 8\\text{ m/s}$. Tần số của sóng là:',
    choices: {
      A: '$5\\text{ Hz}$',
      B: '$10\\text{ Hz}$',
      C: '$15\\text{ Hz}$',
      D: '$20\\text{ Hz}$'
    },
    key: 'B',
    explanation: 'Với hai đầu cố định: $l = k \\frac{\\lambda}{2} = k \\frac{v}{2f}$. Với 3 bụng sóng $\\Rightarrow k = 3$. Thay số: $1{,}2 = 3 \\cdot \\frac{8}{2f} = \\frac{12}{f} \\Rightarrow f = \\frac{12}{1{,}2} = 10\\text{ Hz}$.',
    sourceReference: 'SGK Vật lý 12 - Bài Sóng dừng',
    status: 'FLAGGED',
    writerKey: 'B',
    solverKey: 'A',
    revisionCount: 1,
    auditNotes: 'CẢNH BÁO LỆCH ĐÁP ÁN: Writer chọn B ($10\\text{ Hz}$), Blind Solver ban đầu chọn A ($5\\text{ Hz}$) do nhầm công thức một đầu cố định một đầu tự do. Đã tự động điều chỉnh lời giải, đề xuất giáo viên xác nhận lại đề bài.'
  },
  {
    id: 4,
    topic: 'Dòng điện xoay chiều',
    level: 'NHAN_BIET',
    stem: 'Đặt điện áp xoay chiều $u = U_0\\cos(\\omega t)$ vào hai đầu cuộn cảm thuần có độ tự cảm $L$. Cảm kháng của cuộn cảm là:',
    choices: {
      A: '$Z_L = \\frac{1}{\\omega L}$',
      B: '$Z_L = \\omega L$',
      C: '$Z_L = \\frac{\\omega}{L}$',
      D: '$Z_L = \\sqrt{\\omega L}$'
    },
    key: 'B',
    explanation: 'Cảm kháng của cuộn cảm thuần được tính bằng công thức $Z_L = \\omega L$.',
    sourceReference: 'SGK Vật lý 12 - Mạch xoay chiều chỉ có cuộn cảm thuần',
    status: 'VERIFIED',
    writerKey: 'B',
    solverKey: 'B',
    revisionCount: 0,
    auditNotes: 'Công thức tiêu chuẩn, không có tính đa nghĩa.'
  },
  {
    id: 5,
    topic: 'Dòng điện xoay chiều',
    level: 'THONG_HIEU',
    stem: 'Mạch điện xoay chiều gồm điện trở $R = 30\\,\\Omega$, cuộn cảm thuần có cảm kháng $Z_L = 80\\,\\Omega$ và tụ điện có dung kháng $Z_C = 40\\,\\Omega$ mắc nối tiếp. Tổng trở $Z$ của mạch là:',
    choices: {
      A: '$70\\,\\Omega$',
      B: '$50\\,\\Omega$',
      C: '$150\\,\\Omega$',
      D: '$10\\,\\Omega$'
    },
    key: 'B',
    explanation: 'Tổng trở mạch RLC nối tiếp: $Z = \\sqrt{R^2 + (Z_L - Z_C)^2} = \\sqrt{30^2 + (80 - 40)^2} = \\sqrt{30^2 + 40^2} = 50\\,\\Omega$.',
    sourceReference: 'SGK Vật lý 12 - Mạch RLC nối tiếp',
    status: 'VERIFIED',
    writerKey: 'B',
    solverKey: 'B',
    revisionCount: 0,
    auditNotes: 'Bộ ba Pytago 30-40-50, tính toán chính xác, các phương án nhiễu phản ánh đúng các lỗi cộng đại số thường gặp.'
  },
  {
    id: 6,
    topic: 'Sóng ánh sáng',
    level: 'THONG_HIEU',
    stem: 'Trong thí nghiệm Y-âng về giao thoa ánh sáng, khoảng cách giữa hai khe là $a = 1\\text{ mm}$, khoảng cách từ mặt phẳng chứa hai khe đến màn quan sát là $D = 2\\text{ m}$. Ánh sáng đơn sắc có bước sóng $\\lambda = 0{,}6\\,\\mu\\text{m}$. Khoảng vân $i$ trên màn là:',
    choices: {
      A: '$0{,}6\\text{ mm}$',
      B: '$1{,}2\\text{ mm}$',
      C: '$2{,}4\\text{ mm}$',
      D: '$3{,}0\\text{ mm}$'
    },
    key: 'B',
    explanation: 'Khoảng vân: $i = \\frac{\\lambda D}{a} = \\frac{0{,}6 \\cdot 10^{-6} \\cdot 2}{1 \\cdot 10^{-3}} = 1{,}2 \\cdot 10^{-3}\\text{ m} = 1{,}2\\text{ mm}$.',
    sourceReference: 'SGK Vật lý 12 - Giao thoa ánh sáng',
    status: 'VERIFIED',
    writerKey: 'B',
    solverKey: 'B',
    revisionCount: 0,
    auditNotes: 'Công thức và đơn vị chuẩn, kiểm định số liệu trùng khớp.'
  },
  {
    id: 7,
    topic: 'Vật lý hạt nhân',
    level: 'VAN_DUNG_CAO',
    stem: 'Biết khối lượng của proton, nơtron và hạt nhân $\\mathrm{^{4}_{2}He}$ lần lượt là $m_p = 1{,}0073\\text{ u}$, $m_n = 1{,}0087\\text{ u}$, và $m_\\alpha = 4{,}0015\\text{ u}$. Cho $1\\text{ u} = 931{,}5\\text{ MeV/c}^2$. Năng lượng liên kết riêng của hạt nhân $\\mathrm{^{4}_{2}He}$ xấp xỉ bằng:',
    choices: {
      A: '$28{,}4\\text{ MeV/nuclôn}$',
      B: '$7{,}1\\text{ MeV/nuclôn}$',
      C: '$14{,}2\\text{ MeV/nuclôn}$',
      D: '$3{,}55\\text{ MeV/nuclôn}$'
    },
    key: 'B',
    explanation: 'Độ hụt khối: $\\Delta m = 2m_p + 2m_n - m_\\alpha = 2(1{,}0073) + 2(1{,}0087) - 4{,}0015 = 0{,}0305\\text{ u}$.\nNăng lượng liên kết: $E_{\\text{lk}} = \\Delta m \\cdot 931{,}5 = 28{,}41\\text{ MeV}$.\nNăng lượng liên kết riêng: $\\varepsilon = \\frac{E_{\\text{lk}}}{A} = \\frac{28{,}41}{4} \\approx 7{,}1\\text{ MeV/nuclôn}$.',
    sourceReference: 'SGK Vật lý 12 - Năng lượng liên kết hạt nhân',
    status: 'FLAGGED',
    writerKey: 'B',
    solverKey: 'A',
    revisionCount: 2,
    auditNotes: 'CẢNH BÁO BẪY ĐÁP ÁN: Phương án A ($28{,}4\\text{ MeV}$) là năng lượng liên kết toàn phần, trong khi đề hỏi năng lượng liên kết RIÊNG (chia cho $A=4$). Blind Solver chỉ ra học sinh rất dễ nhầm giữa A và B. Đã giữ B làm đáp án chính thức.'
  },
  {
    id: 8,
    topic: 'Sóng cơ & Sóng âm',
    level: 'NHAN_BIET',
    stem: 'Đặc trưng sinh lý của âm bao gồm:',
    choices: {
      A: 'Độ cao, độ to, âm sắc',
      B: 'Tần số, mức cường độ âm, đồ thị dao động âm',
      C: 'Tốc độ truyền âm, bước sóng, biên độ âm',
      D: 'Năng lượng âm, công suất âm, cường độ âm'
    },
    key: 'A',
    explanation: 'Đặc trưng sinh lý của âm gồm 3 yếu tố: Độ cao (gắn liền với tần số), Độ to (gắn liền với mức cường độ âm) và Âm sắc (gắn liền với đồ thị dao động âm).',
    sourceReference: 'SGK Vật lý 12 - Đặc trưng sinh lý của âm',
    status: 'VERIFIED',
    writerKey: 'A',
    solverKey: 'A',
    revisionCount: 0,
    auditNotes: 'Phân biệt chính xác giữa đặc trưng vật lý và đặc trưng sinh lý theo chuẩn chương trình.'
  }
];

// ============================================================================
// MOCK IMPLEMENTATION (Simulates multi-stage generation, delay & RTC)
// ============================================================================
const MOCK_PDF_DATA_URL = `data:application/pdf;base64,${btoa(
  '%PDF-1.4\n1 0 obj<<>>endobj\n2 0 obj<< /Type /Catalog /Pages 3 0 R >>endobj\n3 0 obj<< /Type /Pages /Count 1 /Kids [4 0 R] >>endobj\n4 0 obj<< /Type /Page /Parent 3 0 R /MediaBox [0 0 595 842] >>endobj\ntrailer<< /Root 2 0 R >>\n%%EOF\n'
)}`;

function mockHash(seed: string): string {
  const clean = seed.replace(/[^a-f0-9]/gi, '').toLowerCase();
  return (clean + '0'.repeat(64)).slice(0, 64);
}

function buildMockPreview(
  jobId: string,
  revision: number,
  contentHash: string,
  approved: boolean,
  status: ExamPreviewState['status'] = 'ready'
): ExamPreviewState {
  const query = `revision=${revision}&contentHash=${contentHash}`;
  const base = `/api/exams/${jobId}/preview`;
  return {
    status,
    revision,
    contentHash,
    sourceHash: mockHash(contentHash.split('').reverse().join('')),
    compilerAvailable: true,
    draft: !approved,
    statusUrl: `${base}?${query}`,
    pdfUrl: status === 'ready' ? MOCK_PDF_DATA_URL : `${base}.pdf?${query}`,
    logUrl: `${base}.log?${query}`,
    ...(status === 'ready' ? { pageCount: 1, pdfHash: mockHash(`${revision}${contentHash}`) } : {}),
  };
}

export class MockExamService implements IExamService {
  private jobs = new Map<string, ExamPackage>();
  private getJob(jobId: string): ExamPackage {
    const job = this.jobs.get(jobId);
    if (!job) throw new Error('Không tìm thấy phiên tạo đề này.');
    return job;
  }

  async startGeneration(params: ExamRequestParams): Promise<{ jobId: string }> {
    const jobId = 'astra-job-' + crypto.randomUUID();
    const contentHash = mockHash(jobId.replace(/-/g, '') + '1');

    // Construct initialized ExamPackage
    const pkg: ExamPackage = {
      examId: jobId,
      title: `Đề Khảo Sát Chất Lượng Môn ${params.subject} - Lớp ${params.grade}`,
      subject: params.subject,
      grade: params.grade,
      durationMinutes: params.durationMinutes,
      totalScore: 10,
      createdAt: new Date().toLocaleDateString('vi-VN'),
      revision: 1,
      contentHash,
      approved: false,
      approval: null,
      hasDrawings: false,
      visualWarnings: [],
      preview: buildMockPreview(jobId, 1, contentHash, false, 'ready'),
      blueprint: {
        subject: params.subject,
        grade: params.grade,
        examType: params.examType,
        title: `Khung Ma Trận Chuẩn Môn ${params.subject}`,
        totalQuestions: params.itemCount,
        durationMinutes: params.durationMinutes,
        levelDistribution: {
          nhanBiet: Math.round(params.itemCount * 0.4),
          thongHieu: Math.round(params.itemCount * 0.3),
          vanDung: Math.round(params.itemCount * 0.2),
          vanDungCao: Math.max(1, Math.round(params.itemCount * 0.1))
        },
        topics: ['Dao động cơ', 'Sóng cơ & Sóng âm', 'Dòng điện xoay chiều', 'Dao động & Sóng điện từ', 'Sóng ánh sáng']
      },
      questions: structuredClone(INITIAL_MOCK_QUESTIONS).map(question => ({
        ...question, examRevision: 1, status: 'PENDING', answerCheck: 'needs_recheck', solverKey: null,
      }))
    };

    this.jobs.set(jobId, pkg);
    return { jobId };
  }

  onProgress(jobId: string, callback: (progress: GenerationProgress) => void): () => void {
    const totalItems = this.getJob(jobId).questions.length;

    const stages = [
      { name: 'Khởi tạo cấu trúc đề thi', durationMs: 1200 },
      { name: 'Tra cứu tài liệu tham khảo', durationMs: 1600 },
      { name: 'Soạn câu hỏi và kiểm tra đáp án', durationMs: 2500 },
      { name: 'Rà soát chất lượng câu hỏi', durationMs: 1800 },
      { name: 'Hoàn thiện đề thi và đáp án', durationMs: 1000 }
    ];

    let timer: ReturnType<typeof setTimeout> | null = null;

    const runStage = (stageIdx: number) => {
      if (stageIdx >= stages.length) {
        callback({
          stage: 5,
          stageName: 'Hoàn tất kiểm định toàn diện',
          percent: 100,
          estimatedSecondsLeft: 0,
          completedItems: totalItems,
          totalItems,
          statusMessage: 'Toàn bộ câu hỏi đã sẵn sàng để giáo viên phê duyệt.'
        });
        return;
      }

      const stageInfo = stages[stageIdx];
      const currentStep = stageIdx + 1;
      const basePercent = (stageIdx / stages.length) * 100;

      // Simulate partial increments within stage
      const completedItems = Math.min(totalItems, Math.round(((stageIdx + 1) / stages.length) * totalItems));
      const previewItem = INITIAL_MOCK_QUESTIONS[stageIdx % INITIAL_MOCK_QUESTIONS.length];

      callback({
        stage: currentStep,
        stageName: stageInfo.name,
        percent: Math.round(basePercent + 15),
        estimatedSecondsLeft: Math.max(5, (stages.length - stageIdx) * 15),
        completedItems,
        totalItems,
        statusMessage: `Đang xử lý ${stageInfo.name.toLowerCase()}...`,
        latestItemPreview: previewItem
      });

      timer = setTimeout(() => {
        runStage(stageIdx + 1);
      }, stageInfo.durationMs);
    };

    // Kick off progression
    runStage(0);

    // Return unsubscribe function
    return () => {
      if (timer) clearTimeout(timer);
    };
  }

  async getExamPackage(jobId: string): Promise<ExamPackage> {
    return structuredClone(this.getJob(jobId));
  }

  private bumpRevision(pkg: ExamPackage, jobId: string) {
    const nextRevision = (pkg.revision ?? 1) + 1;
    const nextHash = mockHash(jobId.replace(/-/g, '') + String(nextRevision));
    pkg.revision = nextRevision;
    pkg.contentHash = nextHash;
    pkg.approved = false;
    pkg.approval = null;
    pkg.questions = pkg.questions.map(question => ({ ...question, examRevision: nextRevision }));
    pkg.preview = buildMockPreview(jobId, nextRevision, nextHash, false, 'not_requested');
  }

  async regenerateQuestion(jobId: string, questionId: number, instruction?: string): Promise<QuestionItem> {
    // Simulate targeted LLM repair for a single item
    await new Promise((res) => setTimeout(res, 1200));

    const pkg = this.getJob(jobId);
    const currentQuestions = pkg.questions;
    const index = currentQuestions.findIndex((q) => q.id === questionId);
    if (index === -1) {
      throw new Error('Không tìm thấy câu hỏi cần thao tác.');
    }

    const current = currentQuestions[index];
    const repaired: QuestionItem = {
      ...current,
      status: 'PENDING',
      answerCheck: 'needs_recheck',
      revisionCount: (current.revisionCount || 0) + 1,
      auditNotes: `Đã tạo lại bản mẫu theo yêu cầu: "${instruction || 'Sửa lại nội dung và đồng bộ đáp án'}".`,
      writerKey: current.key,
      solverKey: null,
    };

    currentQuestions[index] = repaired;
    this.bumpRevision(pkg, jobId);
    return currentQuestions[index];
  }

  async updateQuestion(jobId: string, updatedQuestion: QuestionItem): Promise<void> {
    const pkg = this.getJob(jobId);
    const currentQuestions = pkg.questions;
    const index = currentQuestions.findIndex((q) => q.id === updatedQuestion.id);
    if (index !== -1) {
      currentQuestions[index] = {
        ...updatedQuestion,
        status: 'PENDING',
        answerCheck: 'needs_recheck',
        writerKey: updatedQuestion.key,
        solverKey: null,
        auditNotes: 'Câu đã chỉnh sửa và cần giải lại trên nội dung mới.',
      };
      this.bumpRevision(pkg, jobId);
    }
  }

  async approveExam(jobId: string, pkg: ExamPackage): Promise<ExamPackage> {
    const stored = this.getJob(jobId);
    stored.approved = true;
    stored.approval = {
      revision: pkg.revision ?? stored.revision ?? 1,
      contentHash: pkg.contentHash ?? stored.contentHash ?? '',
      reviewer: 'local-teacher',
      approvedAt: new Date().toISOString(),
    };
    if (stored.preview) {
      stored.preview = { ...stored.preview, draft: false };
    }
    return structuredClone(stored);
  }

  async requestPreview(jobId: string, binding: { revision: number; contentHash: string }): Promise<ExamPreviewState> {
    const stored = this.getJob(jobId);
    const ready = buildMockPreview(jobId, binding.revision, binding.contentHash, Boolean(stored.approved), 'ready');
    stored.preview = ready;
    return structuredClone(ready);
  }

  async getPreviewStatus(jobId: string, binding: { revision: number; contentHash: string }): Promise<ExamPreviewState> {
    return this.requestPreview(jobId, binding);
  }

  async getPreviewLog(): Promise<string> {
    return 'Mock LaTeX preview compiled with 0 errors.';
  }

  async downloadExport(jobId: string, type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: ExportFormat): Promise<void> {
    const pkg = this.getJob(jobId);
    const title = pkg.title;
    const filename = `${title}_${type}.${format === 'docx' ? 'doc' : format}`;

    let content = `==========================================================\n`;
    content += `${title.toUpperCase()}\n`;
    content += `Môn: ${pkg.subject} | Lớp: ${pkg.grade}\n`;
    content += `Thời gian: ${pkg.durationMinutes} phút (Không kể phát đề)\n`;
    content += `Chế độ xuất: ${type}\n`;
    content += `==========================================================\n\n`;

    pkg.questions.forEach((q, idx) => {
      content += `Câu ${idx + 1}: ${q.stem.replace(/\\text\{([^}]+)\}/g, '$1')}\n`;
      content += `  A. ${q.choices.A}\n`;
      content += `  B. ${q.choices.B}\n`;
      content += `  C. ${q.choices.C}\n`;
      content += `  D. ${q.choices.D}\n`;

      if (type === 'TEACHER_KEY') {
        content += `  --> Đáp án: [ ${q.key} ] | Mức độ: ${q.level}\n`;
        content += `  --> Hướng dẫn giải: ${q.explanation}\n`;
        if (q.auditNotes) {
          content += `  --> Kiểm định ASTRA: ${q.auditNotes}\n`;
        }
      }
      content += `\n`;
    });

    const blob = format === 'pdf'
      ? new Blob([atob(MOCK_PDF_DATA_URL.split(',')[1])], { type: 'application/pdf' })
      : new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}

export class ApiError extends Error {
  code: string;
  status?: number;
  details?: unknown;
  constructor(message: string, code = 'request_failed', status?: number, details?: unknown) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

const apiBaseUrl = import.meta.env?.VITE_API_BASE_URL ?? '/api';

export function resolveApiUrl(pathOrUrl: string, baseUrl: string = apiBaseUrl): string {
  if (/^(https?:|blob:|data:)/i.test(pathOrUrl)) return pathOrUrl;
  const normalizedBase = baseUrl.replace(/\/+$/, '');
  if (pathOrUrl === '/api' || pathOrUrl.startsWith('/api/')) {
    const originPrefix = normalizedBase.endsWith('/api')
      ? normalizedBase.slice(0, -'/api'.length)
      : normalizedBase;
    return `${originPrefix}${pathOrUrl}`;
  }
  const cleanPath = pathOrUrl.replace(/^\/+/, '');
  return normalizedBase ? `${normalizedBase}/${cleanPath}` : `/${cleanPath}`;
}

function normalizePreview(
  preview: ExamPreviewState | undefined,
  baseUrl: string
): ExamPreviewState | undefined {
  if (!preview) return undefined;
  return {
    ...preview,
    statusUrl: preview.statusUrl ? resolveApiUrl(preview.statusUrl, baseUrl) : preview.statusUrl,
    pdfUrl: preview.pdfUrl ? resolveApiUrl(preview.pdfUrl, baseUrl) : preview.pdfUrl,
    logUrl: preview.logUrl ? resolveApiUrl(preview.logUrl, baseUrl) : preview.logUrl,
  };
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(url, init); }
  catch { throw new ApiError('Không kết nối được máy chủ. Thầy cô vui lòng thử lại.', 'network_error'); }
  let body: Record<string, unknown> = {};
  try {
    body = await response.json() as Record<string, unknown>;
  } catch {
    if (!response.ok) {
      throw new ApiError(
        humanizeErrorMessage(response.statusText || 'Request failed', 'request_failed'),
        'request_failed',
        response.status
      );
    }
  }
  if (!response.ok) {
    const err = body.error as { code?: string; message?: string; details?: unknown } | undefined;
    const code = err?.code || 'request_failed';
    throw new ApiError(
      humanizeErrorMessage(err?.message || JSON.stringify(body.detail || body), code),
      code,
      response.status,
      err?.details
    );
  }
  return body as T;
}

export interface BackendHealth {
  status?: string;
  demoMode?: boolean;
  providerConfigured?: boolean;
  latexCompilerAvailable?: boolean;
}

export async function getBackendHealth(): Promise<BackendHealth | null> {
  try {
    return await requestJson<BackendHealth>(`${apiBaseUrl}/health`);
  } catch {
    return null;
  }
}

export async function getExamFormats(): Promise<ExamFormat[]> {
  const catalog = await requestJson<{ formats: ExamFormat[] }>(`${apiBaseUrl}/exam-formats`);
  return catalog.formats;
}

export class ApiExamService implements IExamService {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  async startGeneration(params: ExamRequestParams): Promise<{ jobId: string }> {
    const { clientRequestId, ...payload } = params;
    return requestJson(`${this.baseUrl}/exams/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Idempotency-Key': clientRequestId || crypto.randomUUID() },
      body: JSON.stringify(payload)
    });
  }

  onProgress(jobId: string, callback: (progress: GenerationProgress) => void): () => void {
    const eventSource = new EventSource(`${this.baseUrl}/exams/${jobId}/events`);
    let stopped = false;
    let polling = false;
    let failures = 0;
    const deliver = (progress: GenerationProgress) => { if (!stopped) callback(progress); };
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        deliver(data);
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    };
    const poll = async () => {
      if (stopped || polling) return;
      polling = true;
      try {
        const data = await requestJson<GenerationProgress>(`${this.baseUrl}/exams/${jobId}/status`);
        failures = 0;
        deliver(data);
      } catch (error) {
        if (++failures >= 3) deliver({ stage: 0, stageName: 'connection', percent: 0, estimatedSecondsLeft: 0,
          completedItems: 0, totalItems: 22, statusMessage: 'Mất kết nối máy chủ', status: 'failed',
          error: { code: 'network_error', message: humanizeErrorMessage(error instanceof Error ? error.message : 'Connection lost', 'network_error') } });
      } finally { polling = false; }
    };
    const timer = setInterval(() => { void poll(); }, 1500);
    void poll();
    return () => { stopped = true; clearInterval(timer); eventSource.close(); };
  }

  async getExamPackage(jobId: string): Promise<ExamPackage> {
    const pkg = await requestJson<ExamPackage>(`${this.baseUrl}/exams/${jobId}`);
    return {
      ...adaptStudentPaper(pkg, this.baseUrl),
      preview: normalizePreview(pkg.preview, this.baseUrl),
    };
  }

  async regenerateQuestion(jobId: string, questionId: number, instruction?: string, revision?: number): Promise<QuestionItem> {
    const pkg = await this.getExamPackage(jobId);
    const updated = await requestJson<ExamPackage>(`${this.baseUrl}/exams/${jobId}/questions/${questionId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction: instruction || 'Sửa câu hỏi và kiểm tra lại lời giải.', revision: revision ?? pkg.revision })
    });
    return adaptStudentPaper(updated, this.baseUrl).questions.find(question => question.id === questionId)!;
  }

  async updateQuestion(jobId: string, updatedQuestion: QuestionItem): Promise<void> {
    await requestJson(`${this.baseUrl}/exams/${jobId}/questions/${updatedQuestion.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: updatedQuestion, revision: updatedQuestion.examRevision })
    });
  }

  async verifyQuestion(jobId: string, questionId: number, revision: number): Promise<void> {
    await requestJson(`${this.baseUrl}/exams/${jobId}/questions/${questionId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revision }),
    });
  }

  async approveExam(jobId: string, pkg: ExamPackage): Promise<ExamPackage> {
    const updated = await requestJson<ExamPackage>(`${this.baseUrl}/exams/${jobId}/approve`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revision: pkg.revision, contentHash: pkg.contentHash, reviewer: 'local-teacher' })
    });
    return {
      ...adaptStudentPaper(updated, this.baseUrl),
      preview: normalizePreview(updated.preview, this.baseUrl),
    };
  }

  async requestPreview(jobId: string, binding: { revision: number; contentHash: string }): Promise<ExamPreviewState> {
    const state = await requestJson<ExamPreviewState>(`${this.baseUrl}/exams/${jobId}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revision: binding.revision, contentHash: binding.contentHash })
    });
    return normalizePreview(state, this.baseUrl)!;
  }

  async getPreviewStatus(jobId: string, binding: { revision: number; contentHash: string }, statusUrl?: string): Promise<ExamPreviewState> {
    const url = statusUrl
      ? resolveApiUrl(statusUrl, this.baseUrl)
      : `${this.baseUrl}/exams/${jobId}/preview?revision=${binding.revision}&contentHash=${encodeURIComponent(binding.contentHash)}`;
    const state = await requestJson<ExamPreviewState>(url);
    return normalizePreview(state, this.baseUrl)!;
  }

  async getPreviewLog(logUrl: string): Promise<string> {
    let response: Response;
    try {
      response = await fetch(resolveApiUrl(logUrl, this.baseUrl));
    } catch {
      return 'Không tải được thông tin chi tiết bản in PDF.';
    }
    if (!response.ok) {
      try {
        const body = await response.json() as { error?: { message?: string } };
        return body.error?.message || `Không đọc được thông tin chi tiết bản in (mã ${response.status}).`;
      } catch {
        return `Không đọc được thông tin chi tiết bản in (mã ${response.status}).`;
      }
    }
    return response.text();
  }

  async downloadExport(jobId: string, type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: ExportFormat): Promise<void> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}/exams/${jobId}/export?type=${type}&format=${format}`);
    } catch {
      throw new ApiError('Không kết nối được máy chủ khi tải tệp.', 'network_error');
    }
    if (!response.ok) {
      let body: { error?: { code?: string; message?: string; details?: unknown } } = {};
      try { body = await response.json(); } catch { /* non-JSON error body */ }
      throw new ApiError(
        humanizeErrorMessage(body.error?.message || 'Export failed', body.error?.code),
        body.error?.code || 'export_failed',
        response.status,
        body.error?.details
      );
    }
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a'); link.href = url;
    const filename = response.headers.get('content-disposition')?.match(/filename="?([a-zA-Z0-9_.-]+)/)?.[1];
    link.download = filename || (type === 'STUDENT_EXAM' ? `de_thi.${format}` : `dap_an.${format}`);
    link.click(); URL.revokeObjectURL(url);
  }
}

// ============================================================
// SERVICE SELECTOR — điều khiển bởi .env
// ============================================================
// Để chuyển sang backend thật:
//   1. Trong file .env, đặt VITE_SERVICE_MODE=api
//   2. Đặt VITE_API_BASE_URL=http://your-backend-url/api
//   3. Restart dev server (npm run dev)
//
// The integrated API also exposes /api/exam-formats, /status and /approve.
// Current locked THPT export formats are student .tex and teacher .json.
// Core endpoints:
//   POST   /api/exams/generate                         → { jobId: string }
//   GET    /api/exams/{jobId}/events                   → SSE stream of GenerationProgress
//   GET    /api/exams/{jobId}                          → ExamPackage
//   POST   /api/exams/{jobId}/questions/{id}/regenerate → QuestionItem
//   PUT    /api/exams/{jobId}/questions/{id}            → void
//   GET    /api/exams/{jobId}/export?type=...&format=... → file download
//
// SSE event format (mỗi data line):
//   { stage, stageName, percent, estimatedSecondsLeft,
//     completedItems, totalItems, statusMessage,
//     latestItemPreview?: QuestionItem }
// ============================================================

const serviceMode = import.meta.env?.VITE_SERVICE_MODE ?? 'api';

export const examService: IExamService =
  serviceMode === 'api'
    ? new ApiExamService(apiBaseUrl)
    : new MockExamService();
