## 1. Applying Computational Thinking: User-Centric Flow

* **Core Problem:** Differentiate product value across target user segments while outperforming competitor generation speeds (**Decomposition**).
* **User Personas:**
    * **Teachers** (AI Beginners): Primary need = Maximum ease of use and zero-friction onboarding (**Abstraction**).
    * **Students** (Tech-savvy): Primary need = Granular customization and low operational cost (**Abstraction**).
    * **Shared Baseline:** Substantially faster and cheaper exam delivery than market alternatives.


* **Bipartite Workflow Architecture:**
    * **Quick Mode:** Instant generation with 2 inputs: subject (11 canon options) and format (THPT, DGNL, or 15-minute test).
    * **Advanced Mode:** Deep configuration: question count by type, difficulty curve, scope/range, time limit, model selection, and verification mode.

## 2. Core Interface Concept & UX Guidelines

* **Platform & Aesthetics:** Desktop-first; light mode; airy, open, minimal, futuristic vibe.
* **Entry Flow:** Onboarding prompt asks: *"Generate quickly?"* $\rightarrow$ Yes (Quick Mode) / No (Direct to Pro Mode).
* **Workspace & Chat:** Standard LLM chat input with document attachment and web search toggles. Renders live exam assembly side-by-side with chat output for real-time visual feedback.
* **Design Anti-Patterns to Avoid:** Restrain animations to reduce eye fatigue. Avoid generic AI interface cliches: excessive corner rounding, red-yellow-green status palettes, oversized typography, and inline status badges on every element.

## 3. Current Build Issues & Action Items

* **Existing Deficiencies:** Generic fonts, visual inconsistencies, matching foreground/background colors, cluttered "tupperware" containers, disproportionately large sidebars, and redundant element labels.
* **Layout Restructure:**
    * Fix cramped workspace: Expand chat and exam canvas to occupy ~80% of screen space (Gemini Browser standard).
    * Relocate main toolbar from the top header to the right sidebar.

* **Visual Polish & Styling:**
    * Replace hard container borders with soft gradients, subtle textures, soft drop shadows, and glassmorphism transparency.
    * Implement light, subtle floating transitions for appearing and disappearing elements.
    * Apply consistent corporate light palette with green accent: **Hue 130–153**, **Saturation 37–52%**, **Value 80–95%**.

* **Case study:**
    * **The design of "Tạo đề" currently has it the wrong way round**. The chat and the exam should take first precedence: large and interactive; currently both are shoved in a tiny box that is very frictional to control.
    * **Take a golden standard: Gemini Browser**. The chat is almost unbound: takes ~80% of screen; important interactive elements have icons; unified design pallete, etc.