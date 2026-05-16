# Image Generation Prompts for the Launch Series

Paste these into Midjourney, DALL-E 3, ChatGPT image-gen, Imagen, Stable Diffusion (SDXL/Flux), or any image agent. Each post has:

- **Hero image** — top of the Substack post + LinkedIn share card (wide, 1200x628 or 1.91:1)
- **Supporting visual** — mid-post diagram or detail shot (square, 1:1)

## Global style anchors (paste at the end of every prompt)

```
Style: modern developer tooling brand aesthetic. Clean, geometric, slightly editorial. Inspired by Stripe Press covers, GitHub blog hero images, Linear product shots, and Increment magazine. Color palette: soft slate-blue background (#0F172A or #1E293B), warm off-white text (#F8FAFC), one accent color (electric green #4ADE80 or warm amber #F59E0B). High contrast type if any. No stock-photo people. No corporate handshakes. No glowing neural networks. No fake brand logos. Negative prompt: cluttered, busy, generic AI art, blurry, low-contrast, lens flare, photorealistic AI portraits, fake brand marks, watermark, signature.
```

## Standing technical constraints (always include)

- **Aspect ratio**: hero = 16:9 or 1.91:1 (LinkedIn share card 1200x628). Supporting = 1:1.
- **No text in image unless explicitly part of prompt** — easier to add real legible text later in Figma / Canva.
- **No fake logos** — if a logo is wanted, leave blank space for the user to overlay the real `repo-context-hooks` mark.

---

## Post 1: Teaser — "Your coding agent has amnesia"

### Hero (1.91:1)

```
A stylized minimalist illustration of a developer's workspace at the moment of context loss. Foreground: a clean code editor window in dark mode showing a half-finished function, three of its variable names already fading into the background. Behind the editor, a translucent ghost-like silhouette of an AI agent (geometric, not humanoid — think a glowing wireframe cube or sphere) is dissolving into a stream of fragmented memory tiles drifting away into the void. To the right side of the frame, a single small Git branch icon stays sharp and in-focus, hinting that the fix is in the repo, not in the agent's head. Composition: rule-of-thirds, left two-thirds is "loss," right one-third is "what survives." Mood: melancholic but hopeful — not horror.

[paste global style anchors here]
```

### Supporting (1:1)

```
Close-up macro of a single line in a terminal: `pip install repo-context-hooks` rendered in crisp monospace font on a dark slate background. The cursor blinks one character past the line. Subtle film grain. The bottom 20% of the frame has a faint, semi-transparent horizontal git commit graph (three nodes connected by lines) as background texture. No other UI chrome.

[paste global style anchors here]
```

---

## Post 2: The Problem — "The 20-30% you lose every compaction"

### Hero (1.91:1)

```
A flat, infographic-style illustration showing the moment of context compaction as a literal data-compression event. Left side: a tall vertical stack of 30+ small, distinct colorful tiles labeled with subtle code icons (a branch icon, a commit hash, a file name, a diff hunk). Center: an arrow pointing right through a stylized prism or funnel labeled "compaction." Right side: a much shorter stack of only 6-8 dull, beige tiles — labeled "summary." The difference in volume and saturation is the entire visual punchline: 70% of the original information is missing. Above the prism, a small floating number "−25%" rendered in the accent color (electric green or warm amber). Style: editorial infographic, think New York Times feature or FiveThirtyEight visualization.

[paste global style anchors here]
```

### Supporting (1:1)

```
Side-by-side comparison of two file icons. Left: a file labeled `~/.claude/MEMORY.md` rendered with a small "machine-local" padlock badge, faintly grayed-out, sitting on a single laptop silhouette. Right: a file labeled `specs/README.md` rendered with a bright Git branch icon, vibrant, connected by short lines to three small silhouettes representing teammates. Below the two files, a thin horizontal divider labeled "the seam." Composition: balanced halves, left feels cold, right feels collaborative.

[paste global style anchors here]
```

---

## Post 3: The Solution — "10 USPs"

### Hero (1.91:1)

```
A clean, isometric illustration of a workspace contract as a literal document floating over an open git repository. The document itself is rendered as a stack of three translucent layered cards labeled (top to bottom) `specs/README.md`, `UBIQUITOUS_LANGUAGE.md`, `CHANGELOG.md`. Four glowing lines flow into the top of the stack from four labeled circular nodes positioned in a horizontal row above: SessionStart, PreCompact, PostCompact, SessionEnd. The git repository underneath is rendered as a stylized 3D folder with a faint commit graph wrapping around it. To the right, a small monitoring dashboard panel shows three sparkline-style charts in the accent color. Composition: centered, balanced, technical-blueprint feel.

[paste global style anchors here]
```

### Supporting (1:1)

```
A clean numbered list visualization. Background: dark slate. Foreground: ten small geometric icons arranged in a 5x2 grid, each in its own card. Icons are abstract glyphs representing the 10 USPs — a git branch (repo-native), a perfect circle (deterministic), four chained nodes (lifecycle hooks), nine connected dots (cross-harness), a small bar chart (self-measuring), a stopwatch with a delta arrow (experiment mode), a single download arrow (one-line install), a padlock (privacy), a check shield (CI-ready), a verified seal (supply-chain). No text labels on the icons. Each card has a subtle accent-colored border. Mood: like a feature grid on a Stripe or Linear marketing page.

[paste global style anchors here]
```

---

## Post 4: Use Cases + Measurable Impact — "Receipts"

### Hero (1.91:1)

```
A photo-realistic close-up of a developer's dual-monitor setup in a dim room. Left monitor: a clean modern monitoring dashboard with three vivid chart cards — a green upward-trending line chart, a horizontal bar chart in warm amber, and a circular progress ring at roughly 87%. Right monitor: a terminal with a faintly visible block of metrics output (do not render legible specific numbers — keep it impressionistic). Foreground: a coffee mug, slightly out of focus, sitting beside a small mechanical keyboard. Mood: confident, late-evening, the moment when the data tells a story. Lighting: cool blue from the monitors, warm desk lamp on the right edge. Composition: 60% left monitor (the chart story), 40% right monitor + desk.

[paste global style anchors here]
```

### Supporting (1:1)

```
An abstract before-and-after split panel. Left half (labeled BEFORE in small caps at the top): a chaotic tangle of intersecting thin lines in a muted gray, with three small "X" marks scattered through it representing failed approaches. Right half (labeled AFTER in small caps): the same lines reorganized into a clean ascending staircase pattern in the accent color, with three small green check marks where the X marks were. A thin vertical line down the center separates the two halves. Below the split, a single horizontal bar labeled "Week-1 uplift" with a fill level at roughly 70%. Mood: optimistic, data-driven, no hype.

[paste global style anchors here]
```

---

## Post 5: Roadmap + How to Contribute

### Hero (1.91:1)

```
A horizontal timeline rendered as a stylized git commit graph stretching across the frame. Six distinct nodes are spaced along the timeline. The first three nodes (left side) are filled in solid accent color and labeled `v0.6`, `v1.0`, `v1.0.x` — these are "shipped." The next two nodes (center) are half-filled and labeled `v1.1`, `v1.2` — these are "in flight." The final node (right side) is a hollow outline labeled with a question mark — "your contribution." Three short branch lines diverge upward from the center, each ending in a small floating card labeled with one of the three community asks: `platform-parity`, `template-pack`, `experiment-data`. Mood: invitational, open, "the road continues."

[paste global style anchors here]
```

### Supporting (1:1)

```
A clean illustration of three small contributor cards arranged vertically. Each card has a number (1, 2, 3) in the top-left corner in the accent color, and a short abstract icon representing the contribution type: card 1 has 9 small platform-logo silhouettes (left blank for legality — just abstract rounded squares), card 2 has stacked-paper templates icon with three different shapes, card 3 has a small histogram chart icon. The three cards are connected by a thin vertical line on the left edge, like a checklist. Background: dark slate, subtle dot grid. Mood: friendly, low-stakes, "pick one and start."

[paste global style anchors here]
```

---

## Recommended generators by post

| Post | Best generator | Why |
|------|---------------|-----|
| 1 (teaser, mood-driven) | Midjourney v6 or Flux | Best at "stylized minimalist illustration" with mood |
| 2 (infographic-style problem viz) | DALL-E 3 or Imagen | Best at clean infographic / chart compositions |
| 3 (isometric workspace contract) | Midjourney v6 | Strong on isometric tech illustration |
| 4 (photo-real workspace + chart screens) | Flux Pro or Imagen | Better photo-realism than MJ for screen content |
| 5 (timeline + contributor cards) | DALL-E 3 | Cleanest at structured-layout illustrations |

## Reusable prefix for any generator

Drop this in front of any prompt above if the generator is producing too-busy or too-photographic output:

```
Editorial illustration in the style of a Stripe Press book cover or Increment magazine feature. Flat-ish 3D, soft shadows, controlled palette, generous negative space, no busy details. Subject should feel diagrammatic and intentional, not photorealistic.
```

## After generating

Hand-edit in Figma or Canva to add:

- The real `repo-context-hooks` logo (top-left or top-right corner)
- The post title in a clean sans-serif (Inter, IBM Plex Sans, or Söhne)
- Your handle / Substack URL in the bottom-right corner
- One clear CTA strip at the bottom for LinkedIn variants (e.g. "github.com/narendranathe/repo-context-hooks")
