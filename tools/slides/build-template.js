// Builds docs/slides/astra-ct-template.pptx: the ASTRA 4-pillar slide template and mockups.
// Run: NODE_PATH=<dir with pptxgenjs and sharp> node tools/slides/build-template.js
// Optional env: OUT (output path), APPLY_THEME_JS (path to the pptx skill's apply_theme.js, writes the palette into the theme).
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const path = require("path");

const OUT = process.env.OUT || path.join(__dirname, "../../docs/slides/astra-ct-template.pptx");

// ---------- design tokens (single source; docs/slides/README.md explains them) ----------
const INK = "0F172A", MUTE = "475569", LINE = "CBD5E1", SURFACE = "F1F5F9", WHITE = "FFFFFF";
const P = {
  problem:  { mid: "BE123C", dark: "881337", tint: "FCE5EA", name: "PROBLEM DEFINITION", short: "Problem definition", role: "Define input, output, scope, metrics" },
  decomp:   { mid: "1D4ED8", dark: "1E3A8A", tint: "E6EDFC", name: "DECOMPOSITION", short: "Decomposition", num: "01", role: "Split a problem into parts" },
  pattern:  { mid: "0B7A5E", dark: "064E3B", tint: "E1F3EC", name: "PATTERN RECOGNITION", short: "Pattern recognition", num: "02", role: "Find what repeats" },
  abstract: { mid: "B45309", dark: "78350F", tint: "FCEEDB", name: "ABSTRACTION", short: "Abstraction", num: "03", role: "Keep the core, drop the noise" },
  algo:     { mid: "6D28D9", dark: "4C1D95", tint: "ECE6FA", name: "ALGORITHMIC DESIGN", short: "Algorithmic design", num: "04", role: "Write steps a machine can run" },
  doing:    { mid: "475569", dark: "1E293B", tint: "ECEFF3", name: "DOING", short: "Doing", role: "Implementation and simulation" },
};
const HEAD = "Cambria", BODY = "Calibri";
const W = 13.333, H = 7.5, MX = 0.6;
const FOOT = "ASTRA  |  CT proposal";

const THEME = {
  name: "ASTRA CT", headFontFace: HEAD, bodyFontFace: BODY,
  colors: { dk1: INK, lt1: WHITE, dk2: MUTE, lt2: SURFACE, accent1: P.decomp.mid, accent2: P.pattern.mid, accent3: P.abstract.mid,
            accent4: P.algo.mid, accent5: P.problem.mid, accent6: P.doing.mid, hlink: P.decomp.mid, folHlink: P.algo.mid },
};

// ---------- glyph pictures (one shape per pillar, so colour is never the only signal) ----------
function glyphSvg(key, color) {
  const body = {
    decomp: `<rect x="28" y="28" width="200" height="200" rx="34" fill="#${color}"/>`,
    pattern: `<circle cx="128" cy="128" r="102" fill="#${color}"/>`,
    abstract: `<polygon points="128,22 238,226 18,226" fill="#${color}" stroke="#${color}" stroke-width="14" stroke-linejoin="round"/>`,
    algo: `<polygon points="128,12 244,128 128,244 12,128" fill="#${color}"/>`,
    problem: `<polygon points="128,14 156,92 240,96 174,148 196,230 128,184 60,230 82,148 16,96 100,92" fill="#${color}" stroke="#${color}" stroke-width="8" stroke-linejoin="round"/>`,
    doing: `<polygon points="68,22 188,22 244,128 188,234 68,234 12,128" fill="#${color}"/>`,
  }[key];
  return `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">${body}</svg>`;
}
async function glyphPng(key, color) {
  const buf = await sharp(Buffer.from(glyphSvg(key, color))).resize(384, 384).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}


// pptxgenjs gives the slide-number placeholder a fixed id (25) and tables a fixed id (8), which collide with
// other shapes on busy slides. PowerPoint then offers to "repair" the file. Renumber every shape id per slide.
async function fixShapeIds(file) {
  const JSZip = require("jszip");
  const fs = require("fs");
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  for (const name of Object.keys(zip.files).filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n))) {
    let n = 0;
    const xml = (await zip.file(name).async("string")).replace(/<p:cNvPr id="\d+"/g, () => `<p:cNvPr id="${++n}"`);
    zip.file(name, xml);
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "ASTRA CT slide template";
  pres.author = "Team Trial and Success";
  pres.company = "CSC10014 HCMUS";
  pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

  const img = {};   // glyph pictures
  for (const k of Object.keys(P)) {
    img[k + "_white"] = await glyphPng(k, "FFFFFF");
    img[k + "_tint"] = await glyphPng(k, P[k].tint);
    img[k + "_mid"] = await glyphPng(k, P[k].mid);
  }

  // ---------- layouts (these show up in PowerPoint under New Slide) ----------
  const footerObjs = (color) => [{ text: { text: FOOT, options: { x: MX, y: 6.98, w: 4, h: 0.3, fontFace: BODY, fontSize: 10, color, margin: 0, valign: "middle" } } }];
  const slideNo = (color) => ({ x: 12.18, y: 6.98, w: 0.55, h: 0.3, fontFace: BODY, fontSize: 10, color, align: "right", margin: 0 });
  const titlePh = (color) => ({ placeholder: { options: { name: "title", type: "title", x: MX, y: 0.5, w: 9.3, h: 1.1, fontFace: HEAD, fontSize: 30, bold: true, color, valign: "top", margin: 0, align: "left" }, text: "" } });

  pres.defineSlideMaster({ title: "COVER", background: { color: INK }, objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 1.6, w: 10.5, h: 1.6, fontFace: HEAD, fontSize: 58, bold: true, color: WHITE, valign: "bottom", margin: 0, align: "left" }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.9, y: 3.4, w: 9.5, h: 0.9, fontFace: BODY, fontSize: 22, color: "CBD5E1", valign: "top", margin: 0, align: "left" }, text: "" } },
    ...footerObjs("94A3B8")] });

  pres.defineSlideMaster({ title: "NEUTRAL", background: { color: WHITE }, objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.5, w: 12.13, h: 1.1, fontFace: HEAD, fontSize: 30, bold: true, color: INK, valign: "top", margin: 0, align: "left" }, text: "" } },
    ...footerObjs(MUTE)], slideNumber: slideNo(MUTE) });

  for (const k of ["problem", "decomp", "pattern", "abstract", "algo"]) {
    const c = P[k];
    const label = (c.num ? c.num + "   " : "") + c.name;
    pres.defineSlideMaster({ title: "PILLAR_" + k.toUpperCase(), background: { color: WHITE }, objects: [
      titlePh(INK),
      { rect: { x: 10.13, y: 0.55, w: 2.6, h: 0.36, fill: { color: c.mid } } },
      { image: { x: 10.25, y: 0.63, w: 0.2, h: 0.2, data: img[k + "_white"], altText: c.short + " glyph" } },
      { text: { text: label, options: { x: 10.55, y: 0.55, w: 2.15, h: 0.36, fontFace: BODY, fontSize: 11, bold: true, color: WHITE, charSpacing: 1, margin: 0, valign: "middle", fit: "none" } } },
      ...footerObjs(MUTE)], slideNumber: slideNo(MUTE) });

    pres.defineSlideMaster({ title: "DIVIDER_" + k.toUpperCase(), background: { color: c.dark }, objects: [
      { image: { x: 8.7, y: 1.9, w: 3.7, h: 3.7, data: img[k + "_tint"], altText: c.short + " glyph" } },
      ...(c.num ? [{ text: { text: c.num, options: { x: 8.7, y: k === "abstract" ? 3.55 : 1.9, w: 3.7, h: k === "abstract" ? 1.7 : 3.7, fontFace: HEAD, fontSize: 88, bold: true, color: c.dark, align: "center", valign: "middle", margin: 0 } } }] : []),
      { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 2.3, w: 7.4, h: 1.3, fontFace: HEAD, fontSize: 50, bold: true, color: WHITE, valign: "bottom", margin: 0, align: "left" }, text: "" } },
      { placeholder: { options: { name: "subtitle", type: "body", x: 0.9, y: 3.8, w: 7.0, h: 1.2, fontFace: BODY, fontSize: 22, color: c.tint, valign: "top", margin: 0, align: "left" }, text: "" } },
      ...footerObjs(c.tint)] });
  }

  // ---------- helpers ----------
  const S = (layout, section) => pres.addSlide({ masterName: layout, sectionTitle: section });
  const title = (s, t) => s.addText(t, { placeholder: "title" });
  const note = (s, t) => s.addNotes(t);
  const tx = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, fontFace: BODY, color: INK, margin: 0, valign: "top" }, o));
  const box = (s, text, x, y, w, h, o) => s.addText(text, Object.assign({ isTextBox: true, shape: pres.shapes.RECTANGLE, x, y, w, h, fontFace: BODY, fontSize: 13, color: INK, align: "center", valign: "middle", margin: 4 }, o));
  const arrow = (s, x1, y1, x2, y2, o) => {
    const o2 = Object.assign({ color: INK, width: 1.5, end: true, dash: null }, o);
    const line = { color: o2.color, width: o2.width };
    if (o2.end) line.endArrowType = "triangle";
    if (o2.dash) line.dashType = o2.dash;
    s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line });
  };
  const levelMeter = (s, lvl) => {
    const x0 = 10.55, y0 = 7.04;
    tx(s, "L" + lvl, { x: x0, y: 6.98, w: 0.3, h: 0.3, fontSize: 10, color: MUTE, bold: true, valign: "middle" });
    for (let i = 0; i < 5; i++) s.addShape(pres.shapes.OVAL, { x: x0 + 0.36 + i * 0.2, y: y0 + 0.02, w: 0.14, h: 0.14, fill: { color: i < lvl ? INK : WHITE }, line: { color: i < lvl ? INK : "94A3B8", width: 1 }, objectName: "Level meter dot " + (i + 1) });
  };
  // pillar tag for use inside a slide (the layouts already carry one in the top-right corner)
  const tag = (s, k, x, y, w) => {
    const c = P[k], label = (c.num ? c.num + "   " : "") + c.name;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: w || 2.6, h: 0.36, fill: { color: c.mid }, line: { color: c.mid, width: 0.5 }, objectName: "Tag " + c.short });
    s.addImage({ data: img[k + "_white"], x: x + 0.12, y: y + 0.08, w: 0.2, h: 0.2, altText: c.short + " glyph" });
    tx(s, label, { x: x + 0.42, y, w: (w || 2.6) - 0.5, h: 0.36, fontSize: 11, bold: true, color: WHITE, charSpacing: 1, valign: "middle" });
  };
  const glyphShape = (s, k, x, y, d, color, o) => {
    const shape = { decomp: pres.shapes.ROUNDED_RECTANGLE, pattern: pres.shapes.OVAL, abstract: pres.shapes.ISOSCELES_TRIANGLE, algo: pres.shapes.DIAMOND, problem: pres.shapes.STAR_5_POINT, doing: pres.shapes.HEXAGON }[k];
    s.addShape(shape, Object.assign({ x, y, w: d, h: d, fill: { color }, line: { color, width: 0.5 }, rectRadius: 0.1, objectName: "Glyph " + P[k].short }, o));
  };

  // ============ 1. COVER ============
  pres.addSection({ title: "Foundations" });
  let s = S("COVER", "Foundations");
  title(s, "Thinking in four pillars");
  s.addText("ASTRA slide template and mockups. Draft for the team.", { placeholder: "subtitle" });
  ["decomp", "pattern", "abstract", "algo"].forEach((k, i) => {
    const x = 0.9 + i * 2.9;
    glyphShape(s, k, x, 5.35, 0.5, P[k].tint);
    tx(s, P[k].num + "   " + P[k].short, { x: x + 0.7, y: 5.35, w: 2.1, h: 0.5, fontSize: 15, bold: true, color: P[k].tint, valign: "middle" });
  });
  note(s, "Layout: COVER (dark). Use once. Replace the title and subtitle placeholders; keep the four pillar glyphs, they introduce the colour language.");

  // ============ 2. PALETTE ============
  s = S("NEUTRAL", "Foundations");
  title(s, "One colour and one shape for every pillar");
  const rows = ["problem", "decomp", "pattern", "abstract", "algo", "doing"];
  ["Dark", "Mid", "Tint"].forEach((t, i) => tx(s, t, { x: 4.55 + i * 1.3, y: 1.7, w: 1.2, h: 0.25, fontSize: 11, bold: true, color: MUTE, align: "center" }));
  rows.forEach((k, i) => {
    const y = 2.05 + i * 0.74, c = P[k];
    s.addImage({ data: img[k + "_mid"], x: MX, y: y + 0.1, w: 0.4, h: 0.4, altText: c.short + " glyph" });
    tx(s, [{ text: c.short, options: { bold: true, fontSize: 16, breakLine: true } }, { text: c.role, options: { fontSize: 12, color: MUTE } }], { x: 1.2, y, w: 3.2, h: 0.6, valign: "middle" });
    [[c.dark, WHITE], [c.mid, WHITE], [c.tint, c.dark]].forEach(([fill, fg], j) => box(s, "#" + fill, 4.55 + j * 1.3, y, 1.2, 0.6, { fill: { color: fill }, color: fg, fontSize: 12, bold: true, line: { color: fill, width: 0.5 } }));
  });
  tx(s, [
    { text: "How to use it", options: { fontFace: HEAD, fontSize: 20, bold: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Mid colour: chips, diagram nodes, table headers. White text on top.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Tint: panel and cell backgrounds. Dark text on top.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Dark: text on tint, divider backgrounds.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Never set Mid text on Tint: Abstraction falls to 4.4:1.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Colour is never the only signal. Every pillar also owns a shape.", options: { bullet: true } },
  ], { x: 8.75, y: 1.95, w: 3.98, h: 4.6, fontSize: 14 });
  note(s, "Layout: NEUTRAL. Reference slide for the palette. All pairs on this slide were checked for WCAG AA contrast (4.5:1) except Mid on Tint, which is banned for text.");

  // ============ 3. TYPE AND PARTS ============
  s = S("NEUTRAL", "Foundations");
  title(s, "Type, spacing and reusable parts");
  [["Slide title", HEAD, 30, true], ["Section head", HEAD, 20, true], ["Body text", BODY, 16, false], ["Caption and table text", BODY, 12, false]].forEach(([lab, f, sz, b], i) => {
    const y = 1.85 + i * 0.95;
    tx(s, lab, { x: MX, y, w: 5.6, h: 0.55, fontFace: f, fontSize: sz, bold: b, valign: "middle" });
    tx(s, f + " " + (b ? "Bold " : "") + sz + " pt", { x: MX, y: y + 0.55, w: 5.6, h: 0.25, fontSize: 11, color: MUTE });
  });
  tx(s, "Margins 0.6 in. Gaps 0.3 in between related blocks, 0.5 in between sections. Titles never end with a full stop. Body text never goes below 14 pt, table and caption text never below 11 pt.", { x: MX, y: 5.7, w: 5.6, h: 0.9, fontSize: 14 });
  // components column
  tx(s, "Components you can copy", { x: 7.1, y: 1.85, w: 5.6, h: 0.4, fontFace: HEAD, fontSize: 20, bold: true });
  tag(s, "pattern", 7.1, 2.5);
  tx(s, "Pillar tag. Already in every pillar layout, top right.", { x: 9.85, y: 2.5, w: 2.88, h: 0.36, fontSize: 12, color: MUTE, valign: "middle" });
  levelMeter(s, 3); // demo placed in footer position; copy it
  tx(s, "Level meter, bottom right. L1 to L5 shows how far the thinking has grown.", { x: 7.1, y: 3.15, w: 5.6, h: 0.5, fontSize: 12, color: MUTE });
  box(s, "PROPOSED", 7.1, 3.8, 1.5, 0.36, { fill: { color: WHITE }, line: { color: INK, width: 1.25 }, fontSize: 11, bold: true, charSpacing: 1 });
  tx(s, "Idea not yet agreed. Outlined tag.", { x: 8.8, y: 3.8, w: 3.93, h: 0.36, fontSize: 12, color: MUTE, valign: "middle" });
  box(s, "[PLACEHOLDER]", 7.1, 4.4, 1.5, 0.36, { fill: { color: WHITE }, line: { color: MUTE, width: 1.25, dashType: "dash" }, fontSize: 11, color: MUTE, italic: true });
  tx(s, "Space the team fills. Dashed box, grey italic text.", { x: 8.8, y: 4.4, w: 3.93, h: 0.36, fontSize: 12, color: MUTE, valign: "middle" });
  box(s, [{ text: "Line of thought. ", options: { bold: true } }, { text: "One sentence that links this slide to the previous one." }], 7.1, 5.05, 5.63, 0.8, { fill: { color: SURFACE }, align: "left", fontSize: 13, margin: 10 });
  note(s, "Layout: NEUTRAL. Fonts are Cambria (titles) and Calibri (body): both ship with PowerPoint and support Vietnamese. To copy a component, select it, copy, paste on your slide.");

  // ============ 4-5. DECOMPOSITION ============
  pres.addSection({ title: "01 Decomposition" });
  s = S("DIVIDER_DECOMP", "01 Decomposition");
  title(s, "Decomposition");
  s.addText("Break a complex problem into smaller, manageable parts", { placeholder: "subtitle" });
  note(s, "Layout: DIVIDER_DECOMP. One per pillar, opens a section. The big number is part of the layout.");

  s = S("PILLAR_DECOMP", "01 Decomposition");
  title(s, "One exam problem splits into four branches");
  const D = P.decomp;
  box(s, "P0   A usable, correct exam", 4.67, 1.85, 4.0, 0.55, { fill: { color: INK }, color: WHITE, bold: true, fontSize: 15 });
  const cols = [
    { h: "P1  Input and data", kids: ["Database contents", "Corpus and matrices"], dashed: false },
    { h: "P2  Formula set", kids: ["Naive LLM loop (baseline)", "Multi-agent system", "Agents and shared frame", "Composer + Retriever", "Pipeline and parameters"], dashed: false },
    { h: "P3  Quality control", kids: ["Quality metrics, RAG", "Cost, quality, time", "Exam diversity", "A: large context", "B: preassigned"], dashed: false },
    { h: "P4  Reach the user", kids: ["UI/UX", "Assistant", "Extra features"], dashed: true },
  ];
  const cw = 2.75, cg = (12.13 - 4 * cw) / 3;
  arrow(s, 6.665, 2.4, 6.665, 2.68, { end: false, color: MUTE });
  arrow(s, 0.6 + cw / 2, 2.68, 0.6 + 3 * (cw + cg) + cw / 2, 2.68, { end: false, color: MUTE });
  cols.forEach((c, i) => {
    const x = 0.6 + i * (cw + cg);
    arrow(s, x + cw / 2, 2.68, x + cw / 2, 2.93, { color: MUTE, dash: c.dashed ? "dash" : null });
    box(s, c.h, x, 2.95, cw, 0.55, c.dashed ? { fill: { color: WHITE }, line: { color: D.mid, width: 1.5, dashType: "dash" }, color: D.dark, bold: true, fontSize: 14 } : { fill: { color: D.mid }, color: WHITE, bold: true, fontSize: 14, line: { color: D.mid, width: 0.5 } });
    c.kids.forEach((k, j) => box(s, k, x, 3.72 + j * 0.55, cw, 0.46, { fill: { color: D.tint }, color: D.dark, fontSize: 13, line: { color: D.tint, width: 0.5 } }));
  });
  tx(s, "Dashed outline = subproblem raised later.", { x: MX, y: 6.55, w: 6, h: 0.25, fontSize: 12, color: MUTE });
  levelMeter(s, 2);
  note(s, "Layout: PILLAR_DECOMP. Style: tree diagram. Root in ink, branches in the pillar's Mid colour, children in its Tint. Replace the labels; keep at most 5 children per branch so the text stays 13 pt.");

  // ============ 6-7. PATTERN ============
  pres.addSection({ title: "02 Pattern recognition" });
  s = S("DIVIDER_PATTERN", "02 Pattern recognition");
  title(s, "Pattern recognition");
  s.addText("Look for similarities, trends and repetitions", { placeholder: "subtitle" });
  note(s, "Layout: DIVIDER_PATTERN.");

  s = S("PILLAR_PATTERN", "02 Pattern recognition");
  title(s, "Patterns we observed and how to find them");
  const PT = P.pattern;
  const hdr = (t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: PT.mid }, fontSize: 14 } });
  const cell = (t, i, extra) => ({ text: t, options: Object.assign({ color: PT.dark, fill: { color: i % 2 ? WHITE : PT.tint }, fontSize: 15 }, extra || {}) });
  const prow = [
    ["Most exams share one format", "Direct template matching", "Inductive"],
    ["A fixed set of question types", "Grouping and classification", "Inductive"],
    ["Each type is written by a similar method", "Feature extraction", "Inductive"],
    ["Topics shift little from year to year", "Trend and sequence analysis", "Inductive + Probabilistic"],
    ["Numbering and answer labels repeat", "Regular expressions (proposed)", "Deductive"],
  ];
  s.addTable([[hdr("What we observe"), hdr("Technique"), hdr("Reasoning")], ...prow.map((r, i) => [cell(r[0], i), cell(r[1], i, { bold: true }), cell(r[2], i)])],
    { x: MX, y: 1.85, w: 12.13, colW: [5.3, 4.1, 2.73], rowH: [0.5, 0.78, 0.78, 0.78, 0.78, 0.78], fontFace: BODY, valign: "middle", margin: 0.12, border: { type: "none" } });
  tx(s, "Technique names follow Slide04 of the course. Reasoning types follow Slide02.", { x: MX, y: 6.2, w: 9, h: 0.3, fontSize: 12, color: MUTE });
  levelMeter(s, 2);
  note(s, "Layout: PILLAR_PATTERN. Style: table. Header in Mid with white text, rows alternate Tint and white, dark text. No cell borders. Keep a row under two lines.");

  // ============ 8-9. ABSTRACTION ============
  pres.addSection({ title: "03 Abstraction" });
  s = S("DIVIDER_ABSTRACT", "03 Abstraction");
  title(s, "Abstraction");
  s.addText("Keep what matters, drop the noise", { placeholder: "subtitle" });
  note(s, "Layout: DIVIDER_ABSTRACT.");

  s = S("PILLAR_ABSTRACT", "03 Abstraction");
  title(s, "Keep the core model, drop the noise");
  const A = P.abstract;
  s.addShape(pres.shapes.RECTANGLE, { x: MX, y: 1.85, w: 7.2, h: 4.55, fill: { color: A.tint }, line: { color: A.tint, width: 0.5 }, objectName: "Formula panel" });
  tx(s, "E = Φ(T, K; θ)", { x: 0.95, y: 2.1, w: 6.5, h: 1.2, fontFace: HEAD, fontSize: 48, bold: true, italic: true, color: A.dark, valign: "middle" });
  tx(s, [
    { text: "T  ", options: { bold: true } }, { text: "what the teacher gives: intent, sample exam, references, template, matrix", options: { breakLine: true, paraSpaceAfter: 10 } },
    { text: "K  ", options: { bold: true } }, { text: "what the app knows: the database", options: { breakLine: true, paraSpaceAfter: 10 } },
    { text: "θ  ", options: { bold: true } }, { text: "the fixed formula set: blueprint rules, difficulty distribution, scoring profile", options: { breakLine: true, paraSpaceAfter: 10 } },
    { text: "E  ", options: { bold: true } }, { text: "the exam package we hand back" },
  ], { x: 0.95, y: 3.55, w: 6.5, h: 2.6, fontSize: 16, color: A.dark });
  tx(s, [
    { text: "Keep", options: { fontFace: HEAD, fontSize: 20, bold: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Input and output schemas", options: { bullet: true, breakLine: true } },
    { text: "The formula set", options: { bullet: true, breakLine: true } },
    { text: "Subject profile rules", options: { bullet: true, breakLine: true, paraSpaceAfter: 18 } },
    { text: "Drop", options: { fontFace: HEAD, fontSize: 20, bold: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Details of one year or one school", options: { bullet: true, breakLine: true } },
    { text: "One-off exceptions", options: { bullet: true, breakLine: true } },
    { text: "Formatting that does not change meaning", options: { bullet: true } },
  ], { x: 8.35, y: 1.95, w: 4.38, h: 4.4, fontSize: 16 });
  levelMeter(s, 2);
  note(s, "Layout: PILLAR_ABSTRACT. Style: one big idea in a Tint panel, plain two-part list beside it. Use this for a formula, a definition or a model. Do not turn the side list into cards.");

  // ============ 10-11. ALGORITHMIC DESIGN ============
  pres.addSection({ title: "04 Algorithmic design" });
  s = S("DIVIDER_ALGO", "04 Algorithmic design");
  title(s, "Algorithmic design");
  s.addText("Write steps a machine can follow", { placeholder: "subtitle" });
  note(s, "Layout: DIVIDER_ALGO.");

  s = S("PILLAR_ALGO", "04 Algorithmic design");
  title(s, "The pipeline, with a bounded repair loop");
  const G = P.algo;
  const ny = 2.85, nh = 1.1, bw = 1.75, dw = 0.95, gap = 0.36;
  const xs = [MX]; // x of each element: box, gate, box, gate, box, gate, box
  const widths = [bw, dw, bw, dw, bw, dw, bw];
  for (let i = 1; i < 7; i++) xs.push(xs[i - 1] + widths[i - 1] + gap);
  const phase = ["1  Plan", "2  Compose", "3  Check", "4  Confirm"];
  [0, 2, 4, 6].forEach((idx, i) => tx(s, phase[i], { x: xs[idx], y: 2.3, w: bw, h: 0.3, fontSize: 13, bold: true, color: G.dark }));
  const node = (idx, text, y, h) => box(s, text, xs[idx], y, bw, h, { fill: { color: G.mid }, color: WHITE, bold: true, fontSize: 14, line: { color: G.mid, width: 0.5 } });
  node(0, "Clarify intent and build the blueprint", ny, nh);
  node(2, "Retriever, then Composer", ny, nh);
  node(4, "Critics", ny, 0.5); node(4, "Solver", ny + 0.6, 0.5);
  node(6, "Teacher approves, then export", ny, nh);
  [1, 3, 5].forEach((idx, i) => s.addText("G" + (i + 1), { isTextBox: true, shape: pres.shapes.DIAMOND, x: xs[idx], y: ny + nh / 2 - 0.45, w: dw, h: 0.9, fill: { color: G.tint }, line: { color: G.mid, width: 1.5 }, color: G.dark, bold: true, fontSize: 14, fontFace: BODY, align: "center", valign: "middle", margin: 0 }));
  const mid = ny + nh / 2;
  [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6]].forEach(([a, b]) => arrow(s, xs[a] + widths[a] + 0.02, mid, xs[b] - 0.02, mid, { color: INK }));
  // repair loops, drawn so they never cross
  const cx = xs[2] + bw / 2, bot = ny + nh;
  const loop = (fromX, toX, y, label, lx, lw) => {
    arrow(s, fromX, bot - 0.1 + 0.1, fromX, y, { end: false, color: G.mid, dash: "dash" });
    arrow(s, fromX, y, toX, y, { end: false, color: G.mid, dash: "dash" });
    arrow(s, toX, y, toX, bot + 0.02, { color: G.mid, dash: "dash" });
    tx(s, label, { x: lx, y: y + 0.08, w: lw, h: 0.3, fontSize: 12, color: G.dark });
  };
  const g1x = xs[1] + dw / 2, g2x = xs[3] + dw / 2, g3x = xs[5] + dw / 2;
  loop(g1x, xs[0] + bw / 2, 4.55, "missing info: ask again", xs[0], 3.0);
  loop(g2x, cx + 0.45, 4.55, "structure error", cx + 0.5, 2.5);
  loop(g3x, cx - 0.45, 5.05, "check failed and rounds left: repair", cx - 0.45, 4.6);
  tx(s, [{ text: "G1 blueprint valid     G2 structure and policy     G3 Solver agrees with the key and Critics pass", options: { breakLine: true, paraSpaceAfter: 6 } }, { text: "When the rounds run out, the item goes to the teacher with a flag.", options: { color: G.dark, bold: true } }], { x: MX, y: 5.75, w: 12.13, h: 0.8, fontSize: 14 });
  levelMeter(s, 4);
  note(s, "Layout: PILLAR_ALGO. Style: process diagram. Solid arrows are the main flow, dashed arrows in the pillar colour are loops. Diamonds are gates, with Tint fill. Parallel steps are stacked inside one box column. Keep loops from crossing.");

  // ============ 12-14. COMBINATIONS ============
  pres.addSection({ title: "Combinations" });
  s = S("NEUTRAL", "Combinations");
  title(s, "Two pillars on one slide: split first, then look for repeats");
  const pw = 5.65;
  [["decomp", MX, "Exam writing splits into three subproblems", "Input and database.  Formula set.  Quality control."],
   ["pattern", MX + pw + 0.83, "Official exams already work this way", "A committee writes, solves blind, challenges and validates."]].forEach(([k, x, head, body]) => {
    const c = P[k];
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.85, w: pw, h: 3.2, fill: { color: c.tint }, line: { color: c.tint, width: 0.5 }, objectName: "Panel " + c.short });
    tag(s, k, x + 0.3, 2.1);
    tx(s, head, { x: x + 0.3, y: 2.75, w: pw - 0.6, h: 0.95, fontFace: HEAD, fontSize: 22, bold: true, color: c.dark });
    tx(s, body, { x: x + 0.3, y: 3.85, w: pw - 0.6, h: 1.0, fontSize: 16, color: c.dark });
  });
  s.addShape(pres.shapes.RIGHT_ARROW, { x: MX + pw + 0.12, y: 3.2, w: 0.6, h: 0.5, fill: { color: INK }, line: { color: INK, width: 0.5 }, objectName: "Arrow between panels" });
  box(s, [{ text: "Together. ", options: { bold: true } }, { text: "The committee pattern tells us what each subproblem becomes: a team of agents with different roles." }], MX, 5.35, 12.13, 0.8, { fill: { color: SURFACE }, align: "left", fontSize: 15, margin: 12 });
  levelMeter(s, 3);
  note(s, "Layout: NEUTRAL with two pillar panels. Each panel carries its own tag, Tint fill and Dark text. The arrow shows the order of thinking. Use the same structure for any pair.");

  s = S("NEUTRAL", "Combinations");
  title(s, "Three pillars in one chain: pattern, abstraction, decomposition");
  const chain = [["pattern", "Most exams share one format", "So the format can be captured once."], ["abstract", "E = Φ(T, K; θ)", "One formula set stands for the whole class of exams."], ["decomp", "Three subproblems", "Input, formula set, quality control."]];
  chain.forEach(([k, head, body], i) => {
    const c = P[k], x = MX + i * 4.165, y = 1.9 + i * 0.85;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 3.8, h: 2.4, fill: { color: c.tint }, line: { color: c.tint, width: 0.5 }, objectName: "Chain block " + c.short });
    tag(s, k, x + 0.2, y + 0.2, 2.6);
    tx(s, head, { x: x + 0.2, y: y + 0.75, w: 3.4, h: 0.7, fontFace: HEAD, fontSize: 18, bold: true, color: c.dark });
    tx(s, body, { x: x + 0.2, y: y + 1.5, w: 3.4, h: 0.75, fontSize: 14, color: c.dark });
    if (i < 2) s.addShape(pres.shapes.CHEVRON, { x: x + 3.86, y: y + 1.0 + 0.45, w: 0.28, h: 0.45, fill: { color: INK }, line: { color: INK, width: 0.5 }, objectName: "Chain arrow" });
  });
  tx(s, "The staircase shows the order of thinking, not the order of the lectures.", { x: MX, y: 6.3, w: 9, h: 0.3, fontSize: 13, color: MUTE });
  levelMeter(s, 2);
  note(s, "Layout: NEUTRAL, staircase of three pillar blocks. Descending steps mean the flow of thinking. Do not use more than three steps.");

  s = S("NEUTRAL", "Combinations");
  title(s, "All four pillars: where each kind of reasoning does its work");
  const mh = (k) => ({ text: (P[k].num + "  ") + P[k].short, options: { bold: true, color: WHITE, fill: { color: P[k].mid }, fontSize: 13, align: "left" } });
  const lab = (t) => ({ text: t, options: { bold: true, color: INK, fill: { color: SURFACE }, fontSize: 13 } });
  const mc = (t, k) => ({ text: t, options: { color: P[k].dark, fill: { color: P[k].tint }, fontSize: 12 } });
  const ks = ["decomp", "pattern", "abstract", "algo"];
  const M = [
    ["Deductive", "Stop criteria: check each agent", "Template match: exam fits the frame", "Schema: every question is valid", "Gates checked by code"],
    ["Inductive", "Split by the roles of a real committee", "Rules drawn from old exams", "Core model from many exams", "Choose the process from experiments"],
    ["Abductive", "Pin a failure on one layer", "Why the naive loop fails", "Find the variable behind the errors", "Repair loop: guess the cause"],
    ["Probabilistic", "Measure cost against quality", "Topic trends over the years", "Pick enough context, drop noise", "Temperature, sampling, diversity"],
    ["Deontic", "Boundaries of agent duty", "Subject constraints", "Policy and licences", "Round limits, teacher approval"],
    ["Spatial / temporal", "Order of the pipeline", "Trends over time", "States", "Parallel, sequential, loopback"],
  ];
  s.addTable([[{ text: "", options: { fill: { color: WHITE } } }, ...ks.map(mh)], ...M.map((r) => [lab(r[0]), ...ks.map((k, j) => mc(r[j + 1], k))])],
    { x: MX, y: 1.8, w: 12.13, colW: [1.85, 2.57, 2.57, 2.57, 2.57], rowH: [0.45, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62], fontFace: BODY, valign: "middle", margin: 0.1, border: { type: "solid", pt: 1.5, color: WHITE } });
  tx(s, "Cell texts are proposals from the ASTRA slide plan. The team should check each one.", { x: MX, y: 6.45, w: 9, h: 0.3, fontSize: 12, color: MUTE });
  note(s, "Layout: NEUTRAL. Style: matrix table. Header cells use each pillar's Mid colour, body cells its Tint, so the column colour reads at a glance. A white 1.5 pt border separates cells. Reasoning rows are grey.");

  // ============ 15-16. DATA AND PROBLEM ============
  pres.addSection({ title: "Data and problem" });
  s = S("NEUTRAL", "Data and problem");
  title(s, "Charts keep the pillar colours and carry their own labels");
  const cstyle = { catAxisLabelFontFace: BODY, catAxisLabelFontSize: 12, catAxisLabelColor: MUTE, valAxisLabelFontFace: BODY, valAxisLabelFontSize: 11, valAxisLabelColor: MUTE,
    valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, showValue: true, dataLabelFontFace: BODY, dataLabelFontSize: 12, dataLabelFontBold: true, dataLabelColor: INK, catAxisLineShow: true, valAxisLineShow: false };
  tx(s, "Slides per pillar", { x: MX, y: 1.8, w: 5.8, h: 0.35, fontFace: HEAD, fontSize: 18, bold: true });
  s.addChart(pres.charts.BAR, [{ name: "Slides", labels: ["Decomposition", "Pattern", "Abstraction", "Algorithmic"], values: [3, 5, 2, 4] }],
    Object.assign({ x: MX, y: 2.2, w: 5.8, h: 3.7, barDir: "col", chartColors: [P.decomp.mid, P.pattern.mid, P.abstract.mid, P.algo.mid], barGapWidthPct: 60, dataLabelPosition: "outEnd", valAxisMaxVal: 7, valAxisMinVal: 0, valAxisMajorUnit: 1 }, cstyle));
  tx(s, "Items passed after each repair round", { x: 6.9, y: 1.8, w: 5.8, h: 0.35, fontFace: HEAD, fontSize: 18, bold: true });
  s.addChart(pres.charts.LINE, [{ name: "Passed", labels: ["Round 0", "Round 1", "Round 2", "Round 3"], values: [40, 62, 71, 74] }],
    Object.assign({ x: 6.9, y: 2.2, w: 5.8, h: 3.7, chartColors: [P.algo.mid], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9, dataLabelPosition: "t", valAxisMaxVal: 100, valAxisMinVal: 0, valAxisMajorUnit: 25 }, cstyle));
  box(s, "SAMPLE DATA. Replace with measured values before presenting.", MX, 6.1, 5.2, 0.4, { fill: { color: WHITE }, line: { color: MUTE, width: 1.25, dashType: "dash" }, color: MUTE, italic: true, fontSize: 12 });
  levelMeter(s, 4);
  note(s, "Layout: NEUTRAL. Chart style: one series, one colour per pillar when categories are pillars; a single Mid colour when the series is one pillar's. Data labels replace the value axis scale, gridlines are quiet, no legend for single series. All numbers on this slide are dummy values and are labelled as such.");

  s = S("PILLAR_PROBLEM", "Data and problem");
  title(s, "Given, find, and how we will know it worked");
  const R = P.problem;
  s.addShape(pres.shapes.RECTANGLE, { x: MX, y: 1.85, w: 5.2, h: 3.7, fill: { color: R.tint }, line: { color: R.tint, width: 0.5 }, objectName: "Statement panel" });
  tx(s, [
    { text: "Given", options: { fontFace: HEAD, fontSize: 20, bold: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Exam intent, sample exam, references, template, matrix, and the app database K.", options: { fontSize: 16, breakLine: true, paraSpaceAfter: 22 } },
    { text: "Find", options: { fontFace: HEAD, fontSize: 20, bold: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "An exam package that is correct in content, correct in form, and usable without rework.", options: { fontSize: 16 } },
  ], { x: 0.95, y: 2.15, w: 4.5, h: 3.2, color: R.dark });
  const ph = (t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: R.mid }, fontSize: 13 } });
  const pc = (t) => ({ text: t, options: { color: INK, fill: { color: WHITE }, fontSize: 13, border: [{ type: "solid", pt: 0.75, color: LINE }, { type: "none" }, { type: "solid", pt: 0.75, color: LINE }, { type: "none" }] } });
  const pv = () => ({ text: "[PLACEHOLDER]", options: { color: MUTE, italic: true, align: "center", fill: { color: WHITE }, fontSize: 12, border: { type: "dash", pt: 1, color: MUTE } } });
  s.addTable([[ph("Metric"), ph("Measured by"), ph("Value")],
    [pc("Answer correctness"), pc("Reference key"), pv()], [pc("Format compliance"), pc("Checked by code"), pv()], [pc("Source validity"), pc("Evidence ids"), pv()],
    [pc("Teacher minutes"), pc("Timer in review"), pv()], [pc("Cost per paper"), pc("Token log"), pv()]],
    { x: 6.1, y: 1.85, w: 6.63, colW: [2.5, 2.2, 1.93], rowH: [0.45, 0.62, 0.62, 0.62, 0.62, 0.62], fontFace: BODY, valign: "middle", margin: 0.1 });
  tx(s, "Targets in the report are goals until a recorded run says otherwise.", { x: 6.1, y: 5.6, w: 6.63, h: 0.5, fontSize: 12, color: MUTE });
  levelMeter(s, 1);
  note(s, "Layout: PILLAR_PROBLEM (red, star glyph). Style: statement panel plus a placeholder table. Empty cells use the dashed placeholder box so nobody reads them as results.");

  // ============ 17-19. FLOW, STATUS, CHECKLIST ============
  pres.addSection({ title: "Flow and checklist" });
  s = S("NEUTRAL", "Flow and checklist");
  title(s, "Five layers: the thinking grows one layer at a time");
  const lv = [["L1", "One function", "Given, find, scope", "E8EDF3", INK], ["L2", "Subproblems", "Input, formulas, quality", "CBD5E1", INK], ["L3", "Agent committee", "Roles and shared frame", "94A3B8", INK], ["L4", "System design", "Corpus, pipeline, parameters", "475569", WHITE], ["L5", "Product", "UI/UX, assistant, features", INK, WHITE]];
  lv.forEach(([l, name, d, fill, fg], i) => {
    const h = 1.3 + i * 0.7, x = MX + i * 2.45, y = 6.4 - h;
    box(s, [{ text: l, options: { fontFace: HEAD, fontSize: 26, bold: true, breakLine: true } }, { text: name, options: { bold: true, fontSize: 16, breakLine: true } }, { text: d, options: { fontSize: 13 } }], x, y, 2.3, h, { fill: { color: fill }, color: fg, align: "left", valign: "top", margin: 10, line: { color: fill, width: 0.5 } });
    if (i === 0) glyphShape(s, "problem", x, y - 0.4, 0.28, P.problem.mid);
    else ["decomp", "pattern", "abstract", "algo"].forEach((k, j) => glyphShape(s, k, x + j * 0.38, y - 0.4, 0.28, P[k].mid));
  });
  note(s, "Layout: NEUTRAL. Staircase = growth of complexity. Layer 1 only defines the problem (star); from layer 2 on all four pillar glyphs appear above the step. Edit the five names to match your section.");

  s = S("NEUTRAL", "Flow and checklist");
  title(s, "A status tag tells the reader what kind of statement this is");
  const st = [["DECIDED", { fill: { color: INK }, color: WHITE, line: { color: INK, width: 1.25 } }, "Nothing is recorded yet. Decisions are added to DECISIONS.md first."],
              ["PROPOSED", { fill: { color: WHITE }, color: INK, line: { color: INK, width: 1.25 } }, "A multi-agent system with a blind Solver.  A corpus built from approved real exams.  A pipeline with a bounded repair loop."],
              ["OPEN", { fill: { color: WHITE }, color: MUTE, italic: true, line: { color: MUTE, width: 1.25, dashType: "dash" } }, "First subject for the MVP.  Approach A or B for diversity.  Citation of the reference paper."]];
  st.forEach(([lab2, style, body], i) => {
    const y = 1.95 + i * 1.45;
    box(s, lab2, MX, y, 2.0, 0.5, Object.assign({ bold: true, fontSize: 14, charSpacing: 1 }, style));
    tx(s, body, { x: 3.0, y: y - 0.02, w: 9.7, h: 1.1, fontSize: 18 });
  });
  note(s, "Layout: NEUTRAL. The three tag styles are solid, outlined and dashed: they differ by shape of border, not just colour. Use them on every slide where a claim could be mistaken for a result.");

  s = S("NEUTRAL", "Flow and checklist");
  title(s, "Authoring checklist");
  tx(s, [{ text: "Do", options: { fontFace: HEAD, fontSize: 22, bold: true, breakLine: true, paraSpaceAfter: 8 } },
    ...["Start from a pillar layout. The tag and colour come with it.", "One message per slide, stated in the title.", "Diagram first: tree, table, pipeline or formula.", "Mark every unmeasured number as a placeholder or sample.", "Add the level meter and a speaker note.", "Check contrast: white on Mid, Dark on Tint."].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1, paraSpaceAfter: 12 } }))],
    { x: MX, y: 1.9, w: 5.8, h: 4.6, fontSize: 18 });
  tx(s, [{ text: "Do not", options: { fontFace: HEAD, fontSize: 22, bold: true, breakLine: true, paraSpaceAfter: 8 } },
    ...["End a title with a full stop.", "Use Mid colour as text on Tint.", "Rely on colour alone: keep the glyph.", "Stack three or more identical cards.", "Put text under 14 pt, or table text under 11 pt.", "Present a target as a result."].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1, paraSpaceAfter: 12 } }))],
    { x: 6.9, y: 1.9, w: 5.83, h: 4.6, fontSize: 18 });
  note(s, "Layout: NEUTRAL. Plain two-column list on purpose: this slide is reference, not decoration.");

  await pres.writeFile({ fileName: OUT });
  await fixShapeIds(OUT);
  if (process.env.APPLY_THEME_JS) {
    const { applyTheme } = require(process.env.APPLY_THEME_JS);
    await applyTheme(OUT, THEME);
    console.log("theme applied");
  } else console.log("theme not applied (set APPLY_THEME_JS to write the palette into the PowerPoint theme)");
  console.log("wrote", OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
