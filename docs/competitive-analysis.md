# Competitive Analysis and USP

## Similar Existing Projects

1. `thedotmack/claude-mem`  
   GitHub: https://github.com/thedotmack/claude-mem  
   Focus: persistent memory archive, capture/compress/retrieve across sessions.

2. `mem0ai/mem0` and OpenMemory  
   GitHub: https://github.com/mem0ai/mem0  
   Product: https://mem0.ai/openmemory  
   Focus: long-term memory infrastructure and MCP memory delivery.

3. Claude Code lifecycle hooks (platform capability, not a product)  
   Docs: https://code.claude.com/docs/en/hooks  
   Focus: event mechanism only.

## Self-Critique

If RepoHandoff were positioned as "another memory layer", it would be low differentiation versus mature products above.

## Revised USP

RepoHandoff is **not** a memory store. It is a deterministic, repository-local handoff protocol:

- lifecycle orchestration (`SessionStart`, `PreCompact`, `PostCompact`, `SessionEnd`)
- dual-document contract (`README.md` + `specs/README.md`)
- issue-aware startup context and compaction checkpoints
- no database, no external service dependency

## Value Proposition

Teams with strict repo workflows get repeatable context continuity without adding a new memory backend or hosted platform.
