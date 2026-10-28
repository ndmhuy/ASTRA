/**
 * ASTRA - Exam Generation & Verification System
 * Data Types and Interface Contracts (Computational Thinking Pillar III: Abstraction)
 *
 * Maps directly to Section 10 ("Computational Thinking III: Abstraction") and Section 12 
 * ("Proposed Multi-Agent Architecture") of the ASTRA Project Report.
 */

export type Subject = 
  | 'Vật Lý'
  | 'Toán Học'
  | 'Hóa Học'
  | 'Sinh Học'
  | 'Tiếng Anh'
  | 'Lịch Sử'
  | 'Địa Lý'
  | 'GDCD / KTPL';

export type ExamType = 
  | 'THPT_STANDARD'     // Đề Tốt nghiệp THPT chuẩn (40 câu - 50 phút)
  | 'DGNL_DHQG'         // Đề Đánh giá năng lực ĐHQG
  | 'MID_TERM'          // Đề kiểm tra giữa kỳ
  | 'CUSTOM';           // Ma trận tùy biến theo giáo viên

export type CognitiveLevel = 
  | 'NHAN_BIET'         // Nhận biết (Recall / Knowledge)
  | 'THONG_HIEU'        // Thông hiểu (Comprehension)
  | 'VAN_DUNG'          // Vận dụng (Application)
  | 'VAN_DUNG_CAO';     // Vận dụng cao (Higher-order Application)

export type VerificationStatus = 
  | 'PENDING'           // Đang chờ kiểm định
  | 'VERIFIED'          // Đã kiểm chứng (Writer, Solver & Appraiser đồng thuận)
  | 'FLAGGED';          // Cần xem xét (Lệch đáp án hoặc vi luận điểm/bẫy)

export interface QuestionChoices {
  A: string;
  B: string;
  C: string;
  D: string;
}

/**
 * Question Item schema (Core Abstraction)
 * Decouples the question's content, answer keys, provenance, and verification trail.
 */
export interface QuestionItem {
  id: number;
  stem: string;                                   // Nội dung câu hỏi (chứa LaTeX)
  choices: QuestionChoices;                       // 4 phương án lựa chọn
  key: 'A' | 'B' | 'C' | 'D';                     // Đáp án chính thức được chốt
  explanation: string;                            // Lời giải chi tiết
  level: CognitiveLevel;                          // Mức độ nhận thức (Bloom)
  topic: string;                                  // Chủ đề / Chương kiến thức
  sourceReference?: string;                       // Trích dẫn SGK hoặc nguồn cơ sở
  status: VerificationStatus;                     // Trạng thái kiểm định
  
  // Multi-Agent Verification Audit Trail (Section 12 of Report)
  writerKey?: 'A' | 'B' | 'C' | 'D';              // Đáp án do Writer khởi tạo
  solverKey?: 'A' | 'B' | 'C' | 'D';              // Đáp án do Blind Solver giải độc lập
  revisionCount?: number;                         // Số vòng chỉnh sửa tự động
  auditNotes?: string;                            // Ghi chú chi tiết từ Appraiser / Blind Solver
}

/**
 * Normalized Exam Blueprint
 */
export interface ExamBlueprint {
  subject: Subject;
  grade: number;
  examType: ExamType;
  title: string;
  totalQuestions: number;
  durationMinutes: number;
  levelDistribution: {
    nhanBiet: number;
    thongHieu: number;
    vanDung: number;
    vanDungCao: number;
  };
  topics: string[];
}

/**
 * Full Exam Package delivered to Teacher for Final Approval
 * (Corresponds to ExamPackage schema in Section 10)
 */
export interface ExamPackage {
  examId: string;
  title: string;
  subject: Subject;
  grade: number;
  durationMinutes: number;
  totalScore: number;
  createdAt: string;
  blueprint: ExamBlueprint;
  questions: QuestionItem[];
}

/**
 * Parameters submitted from UI Screen 1 (Configuration Hub)
 */
export interface ExamRequestParams {
  subject: Subject;
  grade: number;
  examType: ExamType;
  durationMinutes: number;
  itemCount: number;
  prompt: string;
  uploadedFiles: string[];
}

/**
 * Real-Time Progress Event emitted by Orchestrator during 5-10 min pipeline
 * (Powers Screen 2: Live Generation Stepper)
 */
export interface GenerationProgress {
  stage: number;               // 1 to 5
  stageName: string;           // Tên bước xử lý
  percent: number;             // 0 to 100%
  estimatedSecondsLeft: number;// Ước lượng giây còn lại
  completedItems: number;      // Số câu đã hoàn tất
  totalItems: number;          // Tổng số câu theo ma trận
  statusMessage: string;       // Thông điệp trạng thái chi tiết
  latestItemPreview?: QuestionItem; // Câu hỏi vừa được kiểm duyệt để xem trước
}
