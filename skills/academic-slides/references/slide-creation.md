# Slide Creation Guide

Practical guide for building academic presentation `.pptx` files within the EvoScientist workspace. Covers setup, academic-oriented layout patterns, color palettes, charts, tables, figures, and quality assurance.

> **CRITICAL: Hex colors in PptxGenJS must NOT have `#` prefix.** Write `"1A1A2E"` not `"#1A1A2E"` — the `#` prefix silently corrupts the .pptx file. This applies to ALL color values: backgrounds, fonts, shapes, chart colors.

When the user has already completed paper planning or writing with the `paper-planning` or `paper-writing` skills, pull directly from the workspace artifacts: pipeline figure sketches, experiment result tables, and the story summary (task → challenge → insight → contribution → advantage) to populate slides.

---

## Creation Workflow

```
1. Install dependencies (if not already in workspace)
2. Choose a color palette and font pairing
3. Define slide masters (title, content, section divider)
4. Build slides one by one (one idea per slide)
5. Add charts, tables, and figures from workspace
6. Export, visually inspect, and iterate
```

---

## Setup

### Dependencies

Install via the `execute` tool:

```bash
npm install -g pptxgenjs

# Optional: icons and image processing
npm install -g react-icons react react-dom sharp

# Text extraction and visual QA (also listed in requirements.txt at the skill root)
pip install "markitdown[pptx]" pillow
```

### Basic Structure

Write the generation script to the workspace using `write_file`, then run it via `execute`:

```javascript
// generate_slides.js — write to workspace, run with: node generate_slides.js
const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";  // 10" x 5.625"
pres.author = "Author Name";
pres.title = "Presentation Title";

let slide = pres.addSlide();
slide.addText("Title Text", {
  x: 0.5, y: 0.5, w: 9, h: 1,
  fontSize: 36, fontFace: "Arial", color: "1A1A2E", bold: true
});

pres.writeFile({ fileName: "talk.pptx" });
```

### Slide Dimensions

| Layout | Width | Height | Use Case |
|--------|-------|--------|----------|
| `LAYOUT_16x9` | 10" | 5.625" | Standard conference talks |
| `LAYOUT_4x3` | 10" | 7.5" | Older projectors, some seminars |
| `LAYOUT_WIDE` | 13.3" | 7.5" | Widescreen with extra space |

Use `LAYOUT_16x9` unless the venue specifies otherwise.

---

## Color Palettes for Academic Talks

Choose a palette that fits your topic. Avoid generic corporate blue — it signals "template, not thought."

| Theme | Primary | Secondary | Accent | Good For |
|-------|---------|-----------|--------|----------|
| **Deep Research** | `1A1A2E` (midnight) | `E8E8E8` (silver) | `E94560` (red accent) | CS, engineering, technical methods |
| **Natural Science** | `2D6A4F` (forest) | `D8F3DC` (mint) | `40916C` (emerald) | Biology, environmental, medical |
| **Data & Analytics** | `1B263B` (dark navy) | `415A77` (slate) | `E0E1DD` (off-white) | ML, statistics, data science |
| **Physical Science** | `3D405B` (charcoal) | `E07A5F` (terracotta) | `F4F1DE` (cream) | Physics, chemistry, materials |
| **Warm Academic** | `5C374C` (plum) | `CE796B` (salmon) | `FAF0E6` (linen) | HCI, social computing, design |
| **Clean Minimal** | `2B2D42` (dark gray) | `EDF2F4` (ice) | `EF233C` (signal red) | Any field, safe default |

**Rules:**
- One color dominates (60-70% visual weight) — usually the background or large shapes
- Accent color used sparingly for emphasis (key results, highlights, arrows)
- Never give all colors equal weight
- Dark backgrounds for title and conclusion slides; light for content slides

**Critical:** Hex colors in PptxGenJS must NOT have `#` prefix. Write `"1A1A2E"` not `"#1A1A2E"` — the prefix corrupts the file.

---

## Typography

### Font Pairings

| Heading | Body | Character |
|---------|------|-----------|
| Georgia | Calibri | Classic academic |
| Arial Black | Arial | Bold and clean |
| Cambria | Calibri | Formal, serif heading |
| Trebuchet MS | Calibri | Modern, geometric |
| Palatino | Garamond | Elegant, humanities |
| Calibri | Calibri Light | Minimal, consistent |

Use widely available fonts only. Custom fonts break when presenting on a different machine.

### Size Hierarchy

| Element | Size | Weight |
|---------|------|--------|
| Slide title | 36-44pt | Bold |
| Section header | 20-24pt | Bold |
| Body text | 16-20pt | Regular |
| Annotations / labels | 14-16pt | Regular or light |
| Source credits | 10-12pt | Light color |

**Absolute minimum:** 14pt for anything on screen. Smaller text is unreadable from the back of a room.

### Text Formatting

```javascript
// Claim-style title (good for academic talks)
slide.addText("Our method reduces error by 40% on challenging scenes", {
  x: 0.5, y: 0.3, w: 9, h: 0.8,
  fontSize: 28, fontFace: "Arial", color: "1A1A2E", bold: true
});

// Body text with bullet points
slide.addText([
  { text: "Outperforms all baselines on 3 benchmarks", options: { bullet: true, breakLine: true } },
  { text: "Runs 2x faster than nearest competitor", options: { bullet: true, breakLine: true } },
  { text: "No additional training data required", options: { bullet: true } }
], {
  x: 0.5, y: 1.5, w: 9, h: 2.5,
  fontSize: 18, fontFace: "Calibri", color: "333333"
});
```

**Never use unicode bullets** (`•`). Use `bullet: true` — unicode creates double bullets.

Use `breakLine: true` between items in text arrays; without it, items run together.

---

## Academic Slide Layouts

These layout patterns are designed for common academic presentation needs. Mix and match based on your talk structure (see [talk-structure.md](talk-structure.md) for narrative guidance). If the user has already used `paper-planning`, the story summary and pipeline figure sketch map directly to these layouts.

### Title Slide (Dark Background)

```javascript
let titleSlide = pres.addSlide();
titleSlide.background = { color: "1A1A2E" };

titleSlide.addText("Your Paper Title Here", {
  x: 0.8, y: 1.5, w: 8.4, h: 1.5,
  fontSize: 36, fontFace: "Georgia", color: "FFFFFF", bold: true, align: "center"
});

titleSlide.addText("Author Name — Affiliation", {
  x: 0.8, y: 3.2, w: 8.4, h: 0.6,
  fontSize: 18, fontFace: "Calibri", color: "CCCCCC", align: "center"
});

titleSlide.addText("Conference Name, 2026", {
  x: 0.8, y: 3.9, w: 8.4, h: 0.5,
  fontSize: 14, fontFace: "Calibri", color: "999999", align: "center"
});
```

### Method Overview (Pipeline Figure + Caption)

```javascript
let methodSlide = pres.addSlide();
methodSlide.addText("Overview: Sparse Temporal Attention Framework", {
  x: 0.5, y: 0.2, w: 9, h: 0.7,
  fontSize: 24, fontFace: "Arial", color: "1A1A2E", bold: true
});

// Pipeline figure — fill most of the slide
methodSlide.addImage({
  path: "figures/pipeline.png",
  x: 0.5, y: 1.0, w: 9, h: 3.8,
  sizing: { type: "contain", w: 9, h: 3.8 }
});

// Minimal caption
methodSlide.addText("Novel components highlighted in red", {
  x: 0.5, y: 4.9, w: 9, h: 0.4,
  fontSize: 12, fontFace: "Calibri", color: "888888", italic: true
});
```

### Results Comparison (Two-Column: Table + Key Takeaway)

```javascript
let resultSlide = pres.addSlide();
resultSlide.addText("Our method achieves state-of-the-art on all benchmarks", {
  x: 0.5, y: 0.2, w: 9, h: 0.7,
  fontSize: 24, fontFace: "Arial", color: "1A1A2E", bold: true
});

// Left: comparison table (60% width)
resultSlide.addTable([
  [
    { text: "Method", options: { bold: true, color: "FFFFFF", fill: { color: "1A1A2E" } } },
    { text: "PSNR ↑", options: { bold: true, color: "FFFFFF", fill: { color: "1A1A2E" } } },
    { text: "SSIM ↑", options: { bold: true, color: "FFFFFF", fill: { color: "1A1A2E" } } },
    { text: "FPS ↑", options: { bold: true, color: "FFFFFF", fill: { color: "1A1A2E" } } }
  ],
  ["Baseline A", "28.3", "0.912", "15"],
  ["Baseline B", "29.1", "0.925", "12"],
  [
    { text: "Ours", options: { bold: true, color: "E94560" } },
    { text: "31.4", options: { bold: true, color: "E94560" } },
    { text: "0.951", options: { bold: true, color: "E94560" } },
    { text: "30", options: { bold: true, color: "E94560" } }
  ]
], {
  x: 0.5, y: 1.1, w: 5.5, h: 2.5,
  fontSize: 14, fontFace: "Calibri",
  border: { pt: 0.5, color: "CCCCCC" },
  colW: [1.5, 1.3, 1.3, 1.4],
  align: "center", valign: "middle"
});

// Right: key takeaway callout (40% width)
resultSlide.addShape(pres.shapes.RECTANGLE, {
  x: 6.3, y: 1.1, w: 3.3, h: 2.5,
  fill: { color: "F5F5F5" }
});

resultSlide.addText([
  { text: "+2.3 dB PSNR\n", options: { fontSize: 32, bold: true, color: "E94560", breakLine: true } },
  { text: "over best baseline\n", options: { fontSize: 14, color: "666666", breakLine: true } },
  { text: "\n2x faster inference", options: { fontSize: 18, bold: true, color: "1A1A2E" } }
], {
  x: 6.5, y: 1.3, w: 2.9, h: 2.1,
  align: "center", valign: "middle"
});
```

### Qualitative Comparison (Side-by-Side Images)

```javascript
let qualSlide = pres.addSlide();
qualSlide.addText("Visual comparison on challenging scenes", {
  x: 0.5, y: 0.2, w: 9, h: 0.7,
  fontSize: 24, fontFace: "Arial", color: "1A1A2E", bold: true
});

// Three columns: Input | Baseline | Ours
let labels = ["Input", "Baseline B", "Ours"];
let images = ["input.png", "baseline.png", "ours.png"];

for (let i = 0; i < 3; i++) {
  let xPos = 0.5 + i * 3.1;
  qualSlide.addImage({ path: `figures/${images[i]}`, x: xPos, y: 1.2, w: 2.9, h: 2.9 });
  qualSlide.addText(labels[i], {
    x: xPos, y: 4.2, w: 2.9, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: "555555", align: "center",
    bold: i === 2  // Bold "Ours" label
  });
}
```

### Section Divider

```javascript
let dividerSlide = pres.addSlide();
dividerSlide.background = { color: "1A1A2E" };

dividerSlide.addText("Experiments", {
  x: 1, y: 2, w: 8, h: 1.5,
  fontSize: 40, fontFace: "Georgia", color: "FFFFFF", bold: true, align: "center"
});

dividerSlide.addShape(pres.shapes.LINE, {
  x: 3.5, y: 3.5, w: 3, h: 0,
  line: { color: "E94560", width: 3 }
});
```

---

## Charts for Academic Data

### Bar Chart (Benchmark Comparison)

```javascript
slide.addChart(pres.charts.BAR, [{
  name: "PSNR",
  labels: ["Method A", "Method B", "Method C", "Ours"],
  values: [28.3, 29.1, 29.8, 31.4]
}], {
  x: 0.5, y: 1.2, w: 9, h: 3.8,
  barDir: "col",
  chartColors: ["415A77", "415A77", "415A77", "E94560"],  // Highlight "Ours"
  showValue: true,
  dataLabelPosition: "outEnd",
  dataLabelColor: "333333",
  catAxisLabelColor: "555555",
  valAxisLabelColor: "555555",
  valGridLine: { color: "E8E8E8", size: 0.5 },
  catGridLine: { style: "none" },
  showLegend: false
});
```

### Line Chart (Training Curves)

```javascript
slide.addChart(pres.charts.LINE, [
  { name: "Ours", labels: ["0", "10k", "20k", "30k", "40k", "50k"], values: [20, 26, 29, 30.5, 31.2, 31.4] },
  { name: "Baseline", labels: ["0", "10k", "20k", "30k", "40k", "50k"], values: [20, 24, 26.5, 27.8, 28.5, 29.1] }
], {
  x: 0.5, y: 1.2, w: 9, h: 3.8,
  lineSmooth: true,
  lineSize: 2,
  chartColors: ["E94560", "999999"],
  showLegend: true, legendPos: "b",
  catAxisTitle: "Training Iterations",
  valAxisTitle: "PSNR (dB)",
  showCatAxisTitle: true,
  showValAxisTitle: true,
  valGridLine: { color: "E8E8E8", size: 0.5 },
  catGridLine: { style: "none" }
});
```

### Pie Chart (Component Analysis)

```javascript
slide.addChart(pres.charts.PIE, [{
  name: "Runtime",
  labels: ["Encoder", "Attention", "Decoder", "Post-processing"],
  values: [15, 45, 30, 10]
}], {
  x: 2, y: 1, w: 6, h: 4,
  showPercent: true,
  chartColors: ["1A1A2E", "E94560", "415A77", "CCCCCC"],
  showLegend: true, legendPos: "b"
});
```

---

## Working with Figures

Figures generated during the research process (pipeline diagrams, result visualizations, qualitative comparisons) should already exist in the workspace. Reference them by their workspace path.

### From File

```javascript
slide.addImage({ path: "figures/pipeline.png", x: 0.5, y: 1, w: 9, h: 4 });
```

### Preserve Aspect Ratio

```javascript
// Calculate dimensions to fit within a bounding box
const origW = 1920, origH = 1080, maxW = 9, maxH = 4;
const scale = Math.min(maxW / origW, maxH / origH);
const w = origW * scale;
const h = origH * scale;
const x = (10 - w) / 2;  // Center horizontally

slide.addImage({ path: "figures/result.png", x: x, y: 1, w: w, h: h });
```

### Contain Mode (Auto Fit)

```javascript
slide.addImage({
  path: "figures/comparison.png",
  x: 0.5, y: 1, w: 9, h: 4,
  sizing: { type: "contain", w: 9, h: 4 }
});
```

### Credit Borrowed Figures

Always add attribution when using figures from other papers:

```javascript
slide.addImage({ path: "figures/related_work.png", x: 1, y: 1, w: 5, h: 3 });
slide.addText("Image: Smith et al., CVPR 2024", {
  x: 1, y: 4.1, w: 5, h: 0.3,
  fontSize: 10, fontFace: "Calibri", color: "999999", italic: true
});
```

---

## Icons

Use icons for visual interest on conceptual slides (motivation, contributions, workflow).

```javascript
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaFlask, FaChartBar, FaRocket } = require("react-icons/fa");

function renderIconSvg(Icon, color, size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(Icon, { color, size: String(size) })
  );
}

async function iconToPng(Icon, color, size = 256) {
  const svg = renderIconSvg(Icon, color, size);
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// Usage
const icon = await iconToPng(FaFlask, "#E94560", 256);
slide.addImage({ data: icon, x: 1, y: 1, w: 0.5, h: 0.5 });
```

Use `size: 256` or higher for crisp rendering. The `w`/`h` in inches controls display size.

---

## Shapes and Visual Elements

```javascript
// Colored rectangle (background block, card)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1, w: 4, h: 3,
  fill: { color: "F5F5F5" }
});

// Accent line (horizontal divider)
slide.addShape(pres.shapes.LINE, {
  x: 0.5, y: 1.2, w: 3, h: 0,
  line: { color: "E94560", width: 3 }
});

// Card with shadow
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3.5, h: 2,
  fill: { color: "FFFFFF" },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.1 }
});

// Semi-transparent overlay
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 5.625,
  fill: { color: "1A1A2E", transparency: 40 }
});
```

**Shadow rules:** `offset` must be non-negative. For upward shadows (e.g., footer bar), use `angle: 270`. Never encode opacity in the hex color string — use the `opacity` property.

**No native gradients.** If you need gradient backgrounds, create a gradient image and use it as a slide background:

```javascript
slide.background = { path: "assets/gradient-bg.png" };
```

---

## Slide Masters (Reusable Templates)

Define masters to enforce consistency across slides:

```javascript
// Dark title master
pres.defineSlideMaster({
  title: "TITLE_MASTER",
  background: { color: "1A1A2E" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.8, w: 8.4, h: 1.5 } } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.8, y: 3.5, w: 8.4, h: 0.8 } } }
  ]
});

// Light content master
pres.defineSlideMaster({
  title: "CONTENT_MASTER",
  background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.2, w: 9, h: 0.7 } } },
    { placeholder: { options: { name: "body", type: "body", x: 0.5, y: 1.1, w: 9, h: 4.0 } } }
  ]
});

// Usage
let slide = pres.addSlide({ masterName: "CONTENT_MASTER" });
slide.addText("Claim-style title here", { placeholder: "title" });
```

---

## Quality Assurance

Run QA via the `execute` tool after generating slides.

### Step 1: Content Verification

```bash
python -m markitdown output.pptx
```

Check for:
- Missing content or wrong slide order
- Placeholder text left behind (e.g., "Your Paper Title Here")
- Mismatched data between slides and the paper's actual results

### Step 2: Visual Inspection

Convert to images and inspect every slide:

```bash
soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
# Creates slide-01.jpg, slide-02.jpg, etc.
```

> **If soffice is not installed**: Install LibreOffice (`brew install --cask libreoffice` on macOS, `apt install libreoffice` on Linux). If pdftoppm is missing: `brew install poppler` / `apt install poppler-utils`. If neither is available, use `python-pptx` to extract slide dimensions and element positions programmatically as a fallback check.

Use `read_file` on the generated images to visually check for:
- Overlapping elements (text through shapes, lines through text)
- Text cut off at edges or overflowing boxes
- Uneven spacing (large gaps in one place, cramped in another)
- Low-contrast text (light text on light background)
- Margins too small (keep at least 0.5" from slide edges)
- Misaligned columns or elements
- Borrowed figures missing attribution

### Step 3: Fix and Re-Verify

The first render is rarely correct. After fixing issues, re-run the generation script and re-inspect affected slides. One fix often creates another problem.

**Do not consider the deck done until a full inspection pass reveals no new issues.**

---

## Frequent Mistakes

| Mistake | Fix |
|---------|-----|
| `color: "#FF0000"` | Remove `#` prefix: `color: "FF0000"` — the prefix corrupts the file |
| Unicode bullets `"• item"` | Use `bullet: true` option — unicode creates double bullets |
| Items concatenated in one line | Use `breakLine: true` between text array items |
| Reusing option objects across calls | Create fresh objects each time (the library mutates objects in-place) |
| Gradient fills in code | No native gradient support — use a gradient PNG as background image |
| Paper figures pasted directly | Redesign for projection: thicker lines, larger labels, higher contrast |
| Same layout on every slide | Vary across two-column, full-image, chart, and section divider layouts |
| Text-only slides | Every slide should have at least one visual element |
| Numbers from paper don't match slides | Cross-check all quantitative values against the source paper before export |

---

## Exporting and Backup

```javascript
// Save to workspace
pres.writeFile({ fileName: "talk.pptx" });
```

Always generate a PDF backup alongside the .pptx:

```bash
soffice --headless --convert-to pdf talk.pptx
```

Both files should be in the workspace. The `.pptx` is the primary deliverable; the `.pdf` is the fallback for equipment issues at the venue.

---

## Integration with Other Skills

| Source Skill | Artifact to Reuse | Slides It Maps To |
|---|---|---|
| `paper-planning` | Story summary (task → challenge → insight → contribution) | Motivation, related work narrative |
| `paper-planning` | Pipeline figure sketch | Method overview slide |
| `paper-planning` | Experiment plan (comparisons + ablations) | Results slides, backup comparison table |
| `paper-writing` | Finalized figures and tables | Method + results slides |
| `paper-review` | Self-review findings, anticipated reviewer concerns | Backup Q&A slides |

When these artifacts exist in the workspace, use them directly — do not recreate from scratch.
