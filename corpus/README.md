# Lecturing exam corpus (private)

Why this exists: prototype papers (S-P) are made by downloading the official papers and transcribing them as the model; the MAS labels difficulty from them. They must stay recoverable here, not only on a Drive or a working branch.

- official/2025-web: official 2025 Toán/Vật lí/Hóa học (two codes each), third-party scans, no text layer. Source URL + Drive id per file in its README.md.
- official/ministry-samples: Ministry 2025 sample exams (scans).
- official/2026-sample: 2026 sample exam (text layer).
- prototypes/<subject>: our generated papers (pdf + tex + Answers.json). Keep the FINAL version per subject and batch only; the Drive is the working copy.
- provincial-toan-unverified: Lecturing-app outputs, provenance unverified, NOT official evidence.
- transcriptions/<subject>/<year>/<code>.md|tex: put transcriptions here, each with a first line `status: ocr-draft | teacher-checked | approved`. Difficulty labels go in separate files, never over the transcription.
- SHA256SUMS.txt: recover or verify any file. README-collection-2026-10-23.md: how the first batch was collected.

Rights: state exam papers, copies from third-party sites; internal evidence only; this repo stays private and the papers never ship in the product.
