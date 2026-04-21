# Animation Plan

This repo treats animation as an optional layer on top of the existing SVG assets.

## Goal

Keep the README and core docs stable while still allowing launch or demo material to use motion when it helps explain the workflow.

## Approach

- Start from the SVG sources already used in the README and diagrams.
- Derive any animated assets from those SVGs instead of authoring separate, README-specific motion files.
- Keep the README image embeds static so the documentation still reads well without animation support.

## Practical Rules

- The README should always work with plain SVGs.
- Animated variants can live alongside the SVGs for demos, social posts, or launch pages.
- If animation tooling changes, the README contract should not need to change.
- Any motion asset should be rebuildable from the SVG source without manual redrawing.

## Scope

This plan is intentionally narrow: it explains how to add motion-friendly assets without making the repository documentation depend on them.
