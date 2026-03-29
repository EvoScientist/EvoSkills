# Gradient Glass Style

## Style ID
gradient-glass

## Style Name
Gradient Glassmorphism Card Style

## Supported Models
- gemini-3-pro-image-preview (best quality)
- gemini-3.1-flash-image-preview (fast)
- gemini-2.5-flash-image (fastest)

## Description
A premium Apple-inspired glassmorphism presentation style with light, airy backgrounds. Features soft white-to-pastel gradient bases with frosted glass containers, subtle 3D accents, and generous whitespace. The overall feel is clean, elegant, modern, and spacious — like an Apple Keynote or a polished SaaS landing page.

## Base Prompt

You are an expert UI/UX presentation designer. Generate a high-fidelity, elegant 16:9 presentation slide. Automatically choose the most visually balanced composition — cover, grid layout, or data visualization.

Visual specifications:
- Background: soft white or very light pastel gradient (white-to-lavender, white-to-soft-blue, white-to-pale-pink) — always LIGHT, never dark or black
- Color palette: soft pastels with one vibrant accent color (teal, indigo, coral, or violet) — clean and premium
- Lighting: soft ambient light, gentle reflections, subtle drop shadows — NO harsh cinematic or neon lighting
- Containers: Bento box grid system with frosted glass material (translucent white, backdrop blur effect, thin light borders, soft shadows, generous internal whitespace)
- 3D objects: minimal, tasteful 3D accents as visual anchors — frosted glass spheres, translucent capsules, soft gradient blobs, or subtle floating shapes; muted and elegant, NOT flashy
- Typography: clean sans-serif fonts (SF Pro, Inter style), dark text on light background for readability; charts use clean donut charts, rounded progress bars, or large accent-colored numbers
- Overall feel: Apple Keynote quality, polished and breathable, Dribbble trending aesthetic, light and airy
- STRICTLY AVOID: dark/black backgrounds, neon glow effects, aurora/northern-lights gradients, heavy 3D rendering, flat 2D cartoon illustrations, any footer/watermark/page number
- Do NOT render meta-labels like "Slogan:" or "Visual:" as visible text on the slide
- Do NOT repeat the same sentence twice on the slide

## Page Templates

### Cover Template
Layout: light pastel gradient background, a subtle frosted glass shape or translucent 3D accent at center, bold dark title text overlaid. Clean and spacious first impression.

Use case: First slide, showing title and theme.

### Content Template
Layout: Bento grid with frosted glass cards on light background. Each card has translucent white fill, thin borders, and soft shadows. Text in dark color for readability. Generous internal whitespace.

Use case: Core concepts, key points, content sections.

### Data Template
Layout: split-screen on light background — left side for text, right side for a clean data visualization with accent colors. Charts use rounded donut charts, capsule progress bars, or large accent-colored numbers.

Use case: Data, statistics, comparative analysis, summaries.

### Comparison Template
Layout: two frosted glass panels side by side on light background. Left panel with neutral gray tones (old approach), right panel with vibrant accent color (new approach). Subtle 3D decorative elements between panels.

Use case: Differentiation, paradigm comparisons.

## Examples

### Cover
```
{Base Prompt}

Generate a cover slide with a light pastel gradient background. Place a subtle frosted glass accent shape or translucent 3D element at center. Overlay with bold dark title text:

[Title]

Keep the composition clean, airy, and spacious. No dark backgrounds.
```

### Content
```
{Base Prompt}

Generate a content slide on a light background. Use Bento grid layout with frosted glass containers (translucent white, thin borders, soft shadows). Organize the following content:

[Content]

Dark text on light cards for readability. Generous whitespace between cards.
```

### Data
```
{Base Prompt}

Generate a data/summary slide on a light background. Split-screen design — left side for the following text, right side for a clean data visualization with accent colors:

[Content]

Use rounded charts and large accent-colored numbers. Keep the overall tone light and elegant.
```

## Technical Parameters

### Image Generation Config
- Model: gemini-3-pro-image-preview (default)
- Aspect ratio: 16:9
- Resolution: 2K (2752x1536) or 4K (5504x3072)
- Response mode: IMAGE

### Recommended Settings
- Resolution: 2K (balance of quality and speed)
- Best for: product launches, tech presentations, startup pitches, SaaS product overviews
