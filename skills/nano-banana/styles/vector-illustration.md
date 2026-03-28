# Vector Illustration Style

## Style ID
vector-illustration

## Style Name
Flat Vector Illustration Style

## Supported Models
- gemini-3-pro-image-preview (best quality)
- gemini-3.1-flash-image-preview (fast)
- gemini-2.5-flash-image (fastest)

## Description
Flat vector illustration style with clean black monoline outlines and a retro, muted color palette. Emphasizes geometric simplification and toy-model charm on a cream/off-white paper texture background. Warm, approachable, and easy to understand.

## Base Prompt

You are an expert illustration designer. Generate a 16:9 flat vector illustration style presentation slide.

Visual specifications:
- Background: cream/off-white with subtle paper texture feel
- Color palette: coral red, mint green, mustard yellow, burnt orange, slate blue — retro and muted tones
- Illustration style: flat vector (Flat Vector Illustration) with clean, uniform-weight black monoline outlines; simple color fills with minimal shadows; absolutely no gradients or 3D rendering
- Composition: horizontal panoramic illustrations occupying top 1/3 of the frame
- Line work: uniform-weight black monoline strokes; all objects have closed black outlines (coloring book style); rounded line endings, no sharp corners
- Geometric simplification: reduce complex objects to basic shapes — trees as lollipops or triangles, buildings as rectangular blocks, windows as neat grid patterns; aim for "toy model" charm, not photorealism
- Space & perspective: flat or slightly elevated 2.5D viewpoint; depth via layer overlap only, no atmospheric perspective; all layers equally sharp
- Decorative elements: radiating lines (sunlight/energy), pill-shaped clouds, dots and stars to balance visual density
- Typography: main title in large bold retro serif; subtitle in all-caps sans-serif inside colored rectangle; body text in clean geometric sans-serif
- STRICTLY AVOID: 3D objects, gradients, glassmorphism, dark backgrounds, photorealistic rendering, any footer/watermark/page number
- Do NOT render meta-labels like "Slogan:" or "Visual:" as visible text on the slide
- Do NOT repeat the same sentence twice on the slide

## Page Templates

### Cover Template
Layout: main title in large retro serif, centered. Top 1/3 features a horizontal panoramic vector illustration scene with simplified geometric buildings, toy-like trees, and decorative elements. Cream/off-white paper texture background.

Use case: First slide, showing title and theme.

### Content Template
Layout: top area has a horizontal illustration decorative strip. Content area uses geometric icons and small vector illustrations alongside text, all with uniform black outlines. Colored rectangle blocks (coral, mint, mustard) separate different key points.

Use case: Core concepts, key points, content sections.

### Data Template
Layout: geometric charts and infographic elements — simplified pie charts, bar charts — all with clear black outlines. Retro muted color palette. Decorative geometric elements (dots, stars, radiating lines) balance the composition.

Use case: Data, statistics, comparative analysis, summaries.

### Comparison Template
Layout: left-right split with two illustration panels. Left panel in muted grays (old approach), right panel in vibrant retro colors (new approach). Both panels maintain monoline black outlines. Decorative elements between panels.

Use case: Differentiation, paradigm comparisons.

## Examples

### Cover
```
{Base Prompt}

Generate a cover slide. Top 1/3: horizontal panoramic vector illustration scene with geometric simplified elements relevant to the topic.

Main title in large retro serif:
[Title]

Subtitle in colored rectangle block, all-caps sans-serif.
Cream/off-white paper texture background.
```

### Content
```
{Base Prompt}

Generate a content slide. Top area: horizontal illustration decorative strip.

Content area with the following key points, each with a simple vector icon, all elements with uniform black outlines:

[Content]

Use colored rectangle blocks (coral red, mint green, mustard yellow) to separate points.
```

### Data
```
{Base Prompt}

Generate a data slide. Use geometric vector chart forms with clear black outlines for the following data:

[Content]

Use retro muted colors, add decorative geometric elements (dots, stars, radiating lines) to balance the composition.
```

## Technical Parameters

### Image Generation Config
- Model: gemini-3-pro-image-preview (default)
- Aspect ratio: 16:9
- Resolution: 2K (2752x1536) or 4K (5504x3072)
- Response mode: IMAGE

### Recommended Settings
- Resolution: 2K (balance of quality and speed)
- Best for: educational presentations, creative proposals, children's content, brand storytelling
