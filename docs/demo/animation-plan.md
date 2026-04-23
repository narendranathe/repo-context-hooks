# Animation Plan

Animation is an optional storytelling layer on top of the SVG diagrams in `assets/diagrams/`.

## Goal

Keep the README crisp and GitHub-friendly while still leaving room for launch assets or demos that explain an interrupted task or a handoff story more clearly with motion.

## Source Of Truth

The static SVG remains the source of truth. Any animated asset should be derived from the same diagrams already used in the README so the docs, launch assets, and social snippets all describe the same workflow.

## Story-Driven Motion

If a team makes animated variants, the motion should clarify a concrete repo-native continuity story such as:

- an interrupted task that gets checkpointed before compact
- a handoff story where the next session resumes from `specs/README.md`
- a before-and-after comparison that shows repeated explanation disappearing once continuity is checked in

## Practical Rules

- Start from the existing SVG sources instead of redrawing scenes for animation.
- Use motion to clarify sequence and state change.
- Do not imply automation the tool does not provide.
- Keep README embeds static even if demo variants exist.
- Build GIF, MP4, APNG, or frame-sequence variants only when a launch surface actually benefits from motion.
- Keep every animated asset rebuildable from versioned repo sources.

## Scope

This plan is intentionally narrow. It protects the static-first documentation contract while making the visuals specific enough that future motion work can stay honest.
