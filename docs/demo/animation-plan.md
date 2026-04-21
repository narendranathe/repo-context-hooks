# Animation Plan

This repo treats animation as an optional layer on top of the existing SVG assets in `assets/diagrams/`.

## Goal

Keep the README and core docs stable while still allowing launch or demo material to use motion when it helps explain the workflow.

## Approach

- Start from the SVG sources already used in the README and diagrams under `assets/diagrams/`.
- Derive any animated assets from those SVGs instead of authoring separate, README-specific motion files.
- Produce concrete outputs like short GIFs, MP4 clips, APNGs, or frame sequences when a demo needs motion.
- Keep the README image embeds static so the documentation still reads well without animation support.

## Practical Rules

- The README should always work with plain SVGs.
- Animated variants can live alongside the SVGs for demos, social posts, or launch pages.
- Use motion to clarify flow, sequence, or state changes, not to imply automation the tool does not provide.
- If animation tooling changes, the README contract should not need to change.
- Any motion asset should be rebuildable from the SVG source without manual redrawing.
- Do not make README rendering depend on animated assets.

## Scope

This plan is intentionally narrow: it explains how to add motion-friendly assets without making the repository documentation depend on them.
