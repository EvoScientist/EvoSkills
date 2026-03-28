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
A premium glassmorphism presentation style blending Apple Keynote minimalism, modern SaaS product design, and glass morphism aesthetics. Features deep void black or ceramic white bases with flowing aurora gradients, frosted glass containers, and gift-quality 3D objects. The overall feel is high-end, immersive, clean, and spacious.

## Base Prompt

You are an expert UI/UX presentation designer. Generate a high-fidelity, futuristic 16:9 presentation slide. Automatically choose the most visually balanced composition — cover, grid layout, or data visualization.

Visual specifications:
- Background: deep void black or pure ceramic white as base, with flowing aurora gradients (neon purple, electric blue, soft coral orange, cyan) as accents
- Color palette: aurora gradient highlights on dark/white base — premium, immersive feel
- Lighting: cinematic volumetric light, soft ray-traced reflections, ambient occlusion
- Containers: Bento box grid system with frosted glass material (blur effect, delicate white edges, soft shadows, generous internal whitespace)
- 3D objects: gift-quality abstract 3D items as visual anchors — polished metal, iridescent acrylic, transparent glass, or soft silicone; shapes like floating capsules, spheres, shields, Mobius strips, or fluid waves
- Typography: clean sans-serif fonts with high contrast; charts use glowing 3D donut charts, capsule progress bars, or floating neon numbers
- Overall feel: Unreal Engine 5 quality, ultra-detailed textures, Dribbble trending aesthetic
- STRICTLY AVOID: flat 2D illustrations, cartoon style, lineal icons, light gray backgrounds without gradients, any footer/watermark/page number
- Do NOT render meta-labels like "Slogan:" or "Visual:" as visible text on the slide
- Do NOT repeat the same sentence twice on the slide

## Page Templates

### Cover Template
Layout: large complex 3D glass object at center, overlaid with bold large text. Background features extended aurora waves. Premium, immersive first impression.

Use case: First slide, showing title and theme.

### Content Template
Layout: Bento grid with 3D icons in small frosted glass cards, text in large cards. Generous internal whitespace. Blur effect on all containers with delicate white edges and soft shadows.

Use case: Core concepts, key points, content sections.

### Data Template
Layout: split-screen — left side for text, right side for a large floating glowing 3D data visualization. Charts use glowing 3D donut charts, capsule progress bars, or floating numbers that look like neon toys.

Use case: Data, statistics, comparative analysis, summaries.

### Comparison Template
Layout: two frosted glass panels side by side. Left panel with muted tones (old approach), right panel with vibrant aurora highlights (new approach). 3D decorative elements between panels.

Use case: Differentiation, paradigm comparisons.

## Examples

### Cover
```
{Base Prompt}

Generate a cover slide. Place a large complex 3D glass object at center, overlay with bold text:

[Title]

Background features extended aurora waves.
```

### Content
```
{Base Prompt}

Generate a content slide. Use Bento grid layout, organize the following content in modular rounded rectangle frosted glass containers:

[Content]
```

### Data
```
{Base Prompt}

Generate a data/summary slide. Split-screen design — left side for the following text, right side for a large floating glowing 3D data visualization:

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
- Best for: product launches, tech presentations, creative proposals, data reports
