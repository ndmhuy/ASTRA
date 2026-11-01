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
  ExamRequestParams,
  GenerationProgress,
  QuestionItem
} from '../types/exam';

export interface IExamService {
  startGeneration(params: ExamRequestParams): Promise<{ jobId: string }>;
  onProgress(jobId: string, callback: (progress: GenerationProgress) => void): () => void;
  getExamPackage(jobId: string): Promise<ExamPackage>;
  regenerateQuestion(jobId: string, questionId: number, instruction?: string): Promise<QuestionItem>;
  updateQuestion(jobId: string, updatedQuestion: QuestionItem): Promise<void>;
  downloadExport(jobId: string, type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: 'docx' | 'pdf'): Promise<void>;
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
export class MockExamService implements IExamService {
  private jobs = new Map<string, ExamPackage>();
  private getJob(jobId: string): ExamPackage {
    const job = this.jobs.get(jobId);
    if (!job) throw new Error(`Exam job ${jobId} not found`);
    return job;
  }

  async startGeneration(params: ExamRequestParams): Promise<{ jobId: string }> {
    const jobId = 'astra-job-' + crypto.randomUUID();
    
    // Construct initialized ExamPackage
    const pkg: ExamPackage = {
      examId: `ASTRA-${params.subject.toUpperCase()}-${Date.now().toString().slice(-4)}`,
      title: `Đề Khảo Sát Chất Lượng Môn ${params.subject} - Lớp ${params.grade}`,
      subject: params.subject,
      grade: params.grade,
      durationMinutes: params.durationMinutes,
      totalScore: 10,
      createdAt: new Date().toLocaleDateString('vi-VN'),
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
      questions: structuredClone(INITIAL_MOCK_QUESTIONS)
    };

    this.jobs.set(jobId, pkg);
    return { jobId };
  }

  onProgress(jobId: string, callback: (progress: GenerationProgress) => void): () => void {
    const totalItems = this.getJob(jobId).questions.length;

    const stages = [
      { name: 'Xây dựng & Khóa Ma Trận Đề (Blueprint Builder)', durationMs: 1200 },
      { name: 'Truy xuất SGK & Ngân hàng tri thức (RAG Engine)', durationMs: 1600 },
      { name: 'Soạn thảo & Giải độc lập (Writer + Blind Solver)', durationMs: 2500 },
      { name: 'Thẩm định sư phạm & Bẫy sai (Appraiser)', durationMs: 1800 },
      { name: 'Đóng gói hồ sơ & Barem chấm điểm (Assembler)', durationMs: 1000 }
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

  async regenerateQuestion(jobId: string, questionId: number, instruction?: string): Promise<QuestionItem> {
    // Simulate targeted LLM repair for a single item
    await new Promise((res) => setTimeout(res, 1200));

    const currentQuestions = this.getJob(jobId).questions;
    const index = currentQuestions.findIndex((q) => q.id === questionId);
    if (index === -1) {
      throw new Error(`Question ${questionId} not found`);
    }

    const current = currentQuestions[index];
    const repaired: QuestionItem = {
      ...current,
      status: 'VERIFIED',
      revisionCount: (current.revisionCount || 0) + 1,
      auditNotes: `Đã tự động tái tạo thành công theo hướng dẫn giáo viên: "${instruction || 'Sửa bẫy sai và đồng bộ đáp án'}". Blind Solver và Appraiser đều đánh giá đạt.`,
      writerKey: current.key,
      solverKey: current.key
    };

    currentQuestions[index] = repaired;
    return repaired;
  }

  async updateQuestion(jobId: string, updatedQuestion: QuestionItem): Promise<void> {
    const currentQuestions = this.getJob(jobId).questions;
    const index = currentQuestions.findIndex((q) => q.id === updatedQuestion.id);
    if (index !== -1) {
      currentQuestions[index] = { ...updatedQuestion };
    }
  }

  async downloadExport(jobId: string, type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: 'docx' | 'pdf'): Promise<void> {
    const pkg = this.getJob(jobId);
    const title = pkg.title;
    const filename = `${title}_${type}.${format === 'docx' ? 'doc' : 'txt'}`;

    let content = `==========================================================\n`;
    content += `${title.toUpperCase()}\n`;
    content += `Môn: ${pkg.subject} | Lớp: ${pkg.grade}\n`;
    content += `Thời gian: ${pkg.durationMinutes} phút (Không kể phát đề)\n`;
    content += `Chế độ xuất: ${type}\n`;
    content += `==========================================================\n\n`;

    pkg.questions.forEach((q, idx) => {
      content += `Câu ${idx + 1}: ${q.stem.replace(/\\text\{([^\}]+)\}/g, '$1')}\n`;
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

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
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

// Production API Adapter Skeleton (connects to FastAPI / Flask backend)
export class ApiExamService implements IExamService {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  async startGeneration(params: ExamRequestParams): Promise<{ jobId: string }> {
    const res = await fetch(`${this.baseUrl}/exams/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    return res.json();
  }

  onProgress(jobId: string, callback: (progress: GenerationProgress) => void): () => void {
    const eventSource = new EventSource(`${this.baseUrl}/exams/${jobId}/events`);
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        callback(data);
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    };
    return () => eventSource.close();
  }

  async getExamPackage(jobId: string): Promise<ExamPackage> {
    const res = await fetch(`${this.baseUrl}/exams/${jobId}`);
    return res.json();
  }

  async regenerateQuestion(jobId: string, questionId: number, instruction?: string): Promise<QuestionItem> {
    const res = await fetch(`${this.baseUrl}/exams/${jobId}/questions/${questionId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction })
    });
    return res.json();
  }

  async updateQuestion(jobId: string, updatedQuestion: QuestionItem): Promise<void> {
    await fetch(`${this.baseUrl}/exams/${jobId}/questions/${updatedQuestion.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedQuestion)
    });
  }

  async downloadExport(jobId: string, type: 'STUDENT_EXAM' | 'TEACHER_KEY' | 'MATRIX', format: 'docx' | 'pdf'): Promise<void> {
    window.open(`${this.baseUrl}/exams/${jobId}/export?type=${type}&format=${format}`, '_blank');
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
// Backend cần implement 4 endpoints:
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

const serviceMode = import.meta.env?.VITE_SERVICE_MODE ?? 'mock';
const apiBaseUrl  = import.meta.env?.VITE_API_BASE_URL  ?? '/api';

export const examService: IExamService =
  serviceMode === 'api'
    ? new ApiExamService(apiBaseUrl)
    : new MockExamService();
