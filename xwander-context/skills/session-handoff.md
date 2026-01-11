---
name: session-handoff
description: Prepare context for session continuation or handoff. Use before ending sessions, when approaching compaction, or when another agent/session needs to continue work.
allowed-tools: Bash, Write, mcp__rag-mcp__write_knowledge
---

# Session Handoff

## When to Use
- Session ending (user leaving)
- Approaching context compaction
- Handing off to another agent
- Switching to different CLI tool
- Before `/clear`

## Process

### 1. Summarize Progress
Document what was accomplished:
```markdown
## Session Summary

### Completed
- [x] Task 1: Brief description
- [x] Task 2: Brief description

### In Progress
- [ ] Task 3: Current state, next step

### Blocked
- [ ] Task 4: Blocker description
```

### 2. Document Decisions
```markdown
## Decisions Made
1. **Decision**: Chose X over Y
   **Rationale**: Because Z
   **Impact**: Affects A, B, C
```

### 3. Note Key Artifacts
```markdown
## Key Files
- `/path/to/file1` - Description
- `/path/to/file2` - Description

## State Files
- `state/global.json` - Current project state
- `state/tasks/in-progress/` - Active tasks
```

### 4. Save to RAG
```bash
rag-cli --write "session-handoff | Project: X, Progress: Y%, Next: Z"
```

Or via MCP:
```
mcp__rag-mcp__write_knowledge(
  content="session summary markdown",
  filename="session-{timestamp}.md",
  category="worklogs"
)
```

## Handoff Document Template

```markdown
# Session Handoff: {Project Name}
**Date**: {timestamp}
**Agent**: {claude/gemini/codex}
**Duration**: ~{X} minutes

## Summary
{2-3 sentence overview}

## Progress
- Completed: {count}
- In Progress: {count}
- Blocked: {count}

## Next Steps
1. {Immediate next action}
2. {Following action}

## Context to Preserve
- {Key insight 1}
- {Key insight 2}

## Files Modified
- {file1}: {change description}

## Commands for Continuation
```bash
{command to resume}
```
```

## Output Format
After handoff preparation:
```
Handoff prepared
  Progress: {summary}
  Next: {primary next step}
  Saved: {location}
```
