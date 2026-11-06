# Cấu trúc mã nguồn ASTRA

Mã nguồn chia theo trách nhiệm: domain dùng chung, baseline, tạo draft, pipeline,
HTTP và benchmark. README ở root chỉ hướng dẫn chạy; tài liệu thiết kế hiện hành ở
[architecture/PIPELINE_PLAN_AND_BENCHMARK.md](architecture/PIPELINE_PLAN_AND_BENCHMARK.md).

## Thư mục chính

```text
ASTRA/
├── src/exam_baseline/
│   ├── core/                 Models, contracts, ma trận, profile, hashing dùng chung
│   ├── config.py             Cấu hình .env, không chứa key cố định
│   ├── providers/            Adapter HTTP model và provider mock
│   ├── baseline/             Luồng một agent để làm đối chứng, CLI và báo cáo Markdown
│   ├── draft/                Composer, schema draft, validation và renderer PNG cũ
│   ├── pipeline/
│   │   ├── agents/           Mỗi agent một file; prompt, response binding, validation
│   │   ├── orchestration/    Điều phối, checkpoint validation, lưu/xuất artifacts
│   │   ├── rendering/        Syntax LaTeX/TikZ, ghép document, compiler
│   │   ├── contracts.py      Request/result, solution/review và budget
│   │   ├── views.py          Dữ liệu riêng cho Illustrator/Solver/Reviewer
│   │   ├── bootstrap.py      Ghép provider live hoặc replay theo vai trò
│   │   ├── runtime.py        Trace, token/call budget và deadline
│   │   └── cli.py            CLI full pipeline
│   ├── api/                  App factory, dependency và routes V1/V2 riêng
│   ├── benchmarks/           Runner, scoring và nhãn chấm; tách khỏi runtime
│   ├── resources/            Prompt baseline và JSON fixtures đóng gói trong wheel
│   └── main.py               Entry point uvicorn hiện có
├── tests/                    Chia cùng nhóm chức năng với src; architecture/ kiểm ranh giới
├── examples/                 Input/replay mẫu của mini, pipeline và HCM
├── scripts/                  Dựng fixtures, HTTP smoke và kiểm repository
├── docs/
│   ├── architecture/         Thiết kế pipeline hiện hành
│   ├── guides/               Hướng dẫn theo định dạng/luồng draft
│   ├── plans/                Kế hoạch dài/ngắn giữ để tham khảo lịch sử
│   ├── archive/              Tài liệu bàn giao người 1 cũ
│   └── reports/              Các report và AI declaration đã có trước refactor
├── inputs/                   Input cá nhân, không đưa lên Git
├── runs/                     Kết quả chạy riêng, không đưa lên Git
└── .venv-win/                Môi trường local, không đưa lên Git
```

## Cần sửa gì thì tìm ở đâu?

| Công việc | Vị trí |
| --- | --- |
| Thêm field ma trận/câu hỏi, kiểm phân bố hoặc điểm | `core/models.py`, `core/validation.py` |
| Thêm profile đề | `core/profiles.py` và validation domain |
| Đổi endpoint/key/model mặc định | `.env`, schema cấu hình ở `config.py` |
| Thêm provider mới | `providers/`, theo `core/contracts.py: LLMProvider` |
| Sửa Composer | `pipeline/agents/composer.py`; phần tạo draft dùng chung ở `draft/composer.py` |
| Sửa Illustrator/Solver/Reviewer | File tương ứng trong `pipeline/agents/` |
| Sửa prompt vai trò | `pipeline/agents/prompts.py`; Composer ở `draft/prompts.py` |
| Đổi schema trả về của agent, bind ID/hash | `pipeline/contracts.py`, `agents/responses.py` |
| Đổi validation đáp án/review | `pipeline/agents/validation.py` |
| Đổi luồng hoặc điều kiện gửi feedback | `pipeline/orchestration/orchestrator.py` |
| Đổi nơi lưu, tên file, điều kiện publish | `pipeline/orchestration/artifacts.py` |
| Kiểm input/checkpoint trước khi xuất | `pipeline/orchestration/validation.py` |
| Đổi bố cục đề LaTeX | `pipeline/rendering/document.py` |
| Đổi tập lệnh LaTeX/TikZ được hỗ trợ | `pipeline/rendering/syntax.py` |
| Đổi cách biên dịch | `pipeline/rendering/compiler.py` |
| Đổi HTTP response/headers | `api/routes_baseline.py`, `api/routes_pipeline.py` |
| Đổi cách chấm benchmark | `benchmarks/scoring.py`, `benchmarks/reviewer.py` |

Các đường dẫn trong bảng tính từ `src/exam_baseline/`. Tests tương ứng nằm ở
`tests/core`, `tests/baseline`, `tests/draft`, `tests/pipeline`, `tests/api`,
`tests/providers`, `tests/benchmarks` và `tests/tooling`.

## Quy tắc mở rộng

- `core/` không import HTTP, agent, provider hoặc benchmark. Core chỉ chứa dữ liệu và
  quy tắc domain dùng chung; tests architecture kiểm ranh giới này.
- Mỗi agent phụ trách nội dung của mình. `agents/base.py` chỉ xử lý transport/schema
  correction; prompt và `ResponseContract` được truyền vào, không chọn role bằng if/else.
- Để thay implementation một vai trò, truyền `PipelineAgents(...)` vào Orchestrator;
  không sửa ba agent khác. Thêm role mới cần contract/config, factory và bước điều phối
  rõ ràng, cùng tests về budget/revision/data view.
- ID/revision/hash do code bind. Solver không nhận đáp án Composer; benchmark gold không
  được import vào runtime agents hoặc orchestration.
- Orchestrator quyết định thứ tự/feedback; `RunArtifacts` quản lý filesystem và xuất file.
  Renderer chỉ ghép source; không gọi model hay tự gửi feedback.
- Giữ policy Reviewer một lượt, phản hồi về Composer tối đa một lần, sau đó người dùng
  kiểm tra bằng mắt. Refactor không thay policy này hay contract JSON hiện hành.

## Entry point và tương thích

Lệnh chính mới là `python -m exam_baseline.baseline.cli`, `python -m exam_baseline.draft.cli`
và `python -m exam_baseline.pipeline.cli`. `exam-baseline`/`exam-pipeline` trỏ trực tiếp
vào implementation tương ứng khi cài package.

Các module root `cli.py`, `mini_cli.py`, `pipeline_cli.py` chỉ là launcher tương thích
cho lệnh cũ. `pipeline/orchestrator.py` giữ import Orchestrator cũ; benchmark launcher cũ
cũng được giữ. Business logic luôn nằm trong thư mục chức năng, không nhân đôi code.
Uvicorn vẫn chạy bằng `exam_baseline.main:app`; routes V1/V2 được giữ nguyên.

Các import nội bộ cũ như `exam_baseline.models`, `exam_baseline.mini` hoặc
`exam_baseline.pipeline.latex` được thay bằng `core.models`, `draft/*` và
`pipeline.rendering/*`. Dùng các module mới khi viết code tích hợp.
