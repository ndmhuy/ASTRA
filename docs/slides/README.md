# ASTRA slide template: design system and mockups

**What this is:** the PowerPoint template and mockup deck for the 4-pillar Computational Thinking slides. **Who it is for:** every member who builds slides from [ct-slide-plan.en.md](../ct-slide-plan.en.md). **Status:** draft by Huy with AI help (2026-11-12), not yet reviewed by the team.

Open [astra-ct-template.pptx](astra-ct-template.pptx). It has 19 mockup slides and 13 layouts. In PowerPoint use **New Slide** and pick a layout; copy any component from the mockups.

## How to start a slide

1. Pick the layout by the slide's main pillar: `PILLAR_DECOMP`, `PILLAR_PATTERN`, `PILLAR_ABSTRACT`, `PILLAR_ALGO`, `PILLAR_PROBLEM`. The tag in the top-right corner and the colour come with the layout.
2. A slide with two or more pillars, or no pillar (wrap-up, status, checklist): use `NEUTRAL` and add pillar tags from mockup slides 12 to 14.
3. Section openers: `DIVIDER_*` (one per pillar). Title page: `COVER`.
4. Write the title as the message of the slide, at most about 45 characters so it stays on one line. No full stop.
5. Add the level meter (L1 to L5, copy it from mockup slide 3) and a speaker note.

## Colour tokens (one colour and one shape per pillar)

| Pillar | Shape | Dark | Mid | Tint |
| :--- | :--- | :--- | :--- | :--- |
| Problem definition | star | `881337` | `BE123C` | `FCE5EA` |
| 01 Decomposition | rounded square | `1E3A8A` | `1D4ED8` | `E6EDFC` |
| 02 Pattern recognition | circle | `064E3B` | `0B7A5E` | `E1F3EC` |
| 03 Abstraction | triangle | `78350F` | `B45309` | `FCEEDB` |
| 04 Algorithmic design | diamond | `4C1D95` | `6D28D9` | `ECE6FA` |
| Doing | hexagon | `1E293B` | `475569` | `ECEFF3` |

Neutrals: ink `0F172A`, muted `475569`, line `CBD5E1`, surface `F1F5F9`, white.

- **Mid** for fills, tags, diagram nodes, table headers, with white text (contrast 5.0:1 or better).
- **Tint** for panels and cell backgrounds, with **Dark** text (7.9:1 or better).
- **Dark** for divider backgrounds. Never put Mid text on Tint (Abstraction drops to 4.4:1).
- Colour is never the only signal: the shape, the label and the position repeat it. Contrast ratios were computed, not eyeballed.

## Type and spacing

| Role | Font | Size |
| :--- | :--- | :--- |
| Slide title | Cambria Bold | 30 pt (dividers 50, cover 58) |
| Section head | Cambria Bold | 20 to 22 pt |
| Body | Calibri | 14 to 18 pt, never below 14 |
| Table, caption, label | Calibri | 11 to 13 pt, never below 11 |

Cambria and Calibri ship with PowerPoint and support Vietnamese. Slide size is 13.33 x 7.5 in (16:9). Margins 0.6 in; gaps 0.3 in within a group, 0.5 in between sections. Left-aligned text; only numbers inside glyphs are centred.

## Scenarios, and which mockup shows them

| Scenario | Mockup slide | Style |
| :--- | :--- | :--- |
| Single pillar, divider | 4, 6, 8, 10 | full-colour background, big glyph with the pillar number |
| Single pillar, diagram | 5 (tree), 11 (process with gates and loops) | Mid nodes, Tint children, dashed = raised later, loops dashed in the pillar colour |
| Single pillar, table | 7 | Mid header, alternating Tint and white rows, no borders |
| Single pillar, concept | 9 | one big idea in a Tint panel, plain list beside it |
| Two pillars | 12 | two panels, each with its own tag and Tint, an arrow for the order of thinking |
| Three pillars | 13 | staircase of three blocks |
| Four pillars | 14 | matrix table: header in each pillar's Mid, cells in its Tint |
| Chart | 15 | native charts; one colour per pillar when categories are pillars; data labels instead of a legend; quiet gridlines |
| Problem and metrics | 16 | statement panel plus a table whose empty cells are dashed placeholders |
| Flow and complexity | 17 | staircase L1 to L5, pillar glyphs above each step |
| Status | 18 | three tag styles: solid DECIDED, outlined PROPOSED, dashed OPEN |
| Reference | 2, 3, 19 | palette, type and components, checklist |

## Components (mockup slide 3)

Pillar tag, level meter, `PROPOSED` outlined tag, `[PLACEHOLDER]` dashed box, "Line of thought" strip. Mark every number that was not measured as a placeholder or as sample data: the charts on slide 15 carry dummy values and say so.

## Rebuild

`tools/slides/build-template.js` generates the deck, so the palette lives in one place (the token block at the top). The `.pptx` is committed on purpose, as the team's starting file; edit the script and rebuild rather than hand-editing the layouts.

```bash
npm install pptxgenjs sharp
NODE_PATH=./node_modules node tools/slides/build-template.js
```

Optional: set `APPLY_THEME_JS` to the pptx skill's `apply_theme.js` so the palette also appears in PowerPoint's colour picker.

## Design choices, with the reasons

- **Pillar identity top-right, not above the title.** A label above every heading adds noise; the title carries the message.
- **No accent lines, side stripes or gradients.** Tint panels and white space separate things.
- **Varied structures.** Tree, table, formula panel, process, staircase, matrix: no slide is a grid of identical cards.
- **One shape per pillar** so a colour-blind reader or a black-and-white print still tells the pillars apart.
- **Placeholders are visible** (dashed) so nobody mistakes a gap for a result.

## Not verified

Rendered and checked only in LibreOffice (fonts substituted by Carlito and Caladea, which match Calibri and Cambria metrics). Not opened in PowerPoint or Keynote. The file passes the pptx validator; contrast ratios were computed with the WCAG formula. Mockup content is taken from the ASTRA slide plan and is a proposal.
