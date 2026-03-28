# Lineal Color Style

## Style ID
lineal-color

## Style Name
Lineal Color — Flat Linear Icon Style

## Supported Models
- gemini-3-pro-image-preview (best quality)
- gemini-3.1-flash-image-preview (fast)
- gemini-2.5-flash-image (fastest)

## Description
NotebookLM-inspired infographic style: light gray/white background, colorful flat illustrations, structured info cards with rich visual density. Combines friendly cartoon-style illustrations (people, robots, trophies) with clean text panels and data cards.

## Base Prompt

Create a professional 16:9 presentation slide. Clean, minimal design — educational and professional, NOT a product launch or marketing deck.

Visual specifications:
- Background: very light gray or white, completely flat, clean, generous whitespace
- Color palette: teal (for accents and labels), dark navy (for main titles), medium gray (for subtitles) — calm and professional
- Illustrations: flat 2D cartoon-style illustrations — friendly, simple, NOT 3D rendered, NOT photorealistic
- Info panels: clean rounded rectangle cards with light border, white fill, bold header + short body text
- Diagrams: simple flow diagrams with teal/blue arrows, flat icon nodes
- Icons: flat 2D icons inside teal or colored circles
- Typography: clear hierarchy — large bold title, medium gray subtitle, small label text; title should fit in 1-2 lines max
- Overall feel: clean technical presentation, like a well-designed university lecture slide
- STRICTLY AVOID: 3D objects, dark backgrounds, aurora/neon glow, glass morphism, sci-fi aesthetics, photorealistic rendering, hex color codes as visible text, achievement highlight cards on cover pages, any footer/watermark/page number
- Do NOT render meta-labels like "Slogan:" or "Visual:" as visible text on the slide
- Do NOT repeat the same sentence twice on the slide

## Page Templates

### Cover Template
Layout: light gray/white background, two-column layout. Left column (40%): a simple flat 2D cartoon illustration (teal/blue color scheme), no text inside the illustration. Right column (60%): text area vertically centered with 3-4 lines — large bold dark title (1-2 lines), medium gray subtitle, small teal label. Title appears only once, never repeated. No achievement cards, flow diagrams, icon panels, or extra elements.

Use case: First slide of the presentation, showing the topic title and core positioning.

### Content Template
Layout: large title at top, content area uses 2-3 column cards or left-text-right-image split layout. Cards contain icons, sub-headers, and short descriptions. Arrows and connectors show flow or comparison relationships.

Use case: Core features, architecture, processes, comparative analysis.

### Data Template
Layout: title at top, center area uses 2-4 large number cards (oversized numbers with small labels) for key metrics, or a clean horizontal timeline/flow chart. Different colors distinguish data items.

Use case: Performance data, milestones, roadmaps, timelines.

### Comparison Template
Layout: left-right split using tables or side-by-side cards comparing "traditional approach vs new approach". Left column uses muted gray tones, right column uses highlighted accent colors.

Use case: Differentiation, paradigm comparisons.

## Examples

### Cover
```
{Base Prompt}

OVERRIDE ALL PREVIOUS LAYOUT INSTRUCTIONS. Generate a minimal cover slide with ONLY the following layout:
- Left 40%: one simple flat 2D cartoon illustration. Teal and blue colors. NO text inside the illustration.
- Right 60%: plain text area, vertically centered, three lines only:
  Line 1 (large bold dark): [Title]
  Line 2 (medium gray): [Subtitle]
  Line 3 (small teal label): [Label]
- DO NOT add achievement cards, feature diagrams, icon panels, or any extra elements.
- DO NOT repeat the title anywhere else on the slide.
```

### Content
```
{Base Prompt}

Generate a content slide. Display a large title at top, then use cards or split-column layout with flat icons for the following content:

[Content]
```

### Data
```
{Base Prompt}

Generate a data visualization slide. Use large number cards or clean charts to highlight the following key metrics:

[Content]
```

## Technical Parameters

### Image Generation Config
- Model: gemini-3-pro-image-preview (default)
- Aspect ratio: 16:9
- Resolution: 2K (2752x1536) or 4K (5504x3072)
- Response mode: IMAGE

### Recommended Settings
- Resolution: 2K (balance of quality and speed)
- Best for: technical talks, academic presentations, product overviews, educational content
