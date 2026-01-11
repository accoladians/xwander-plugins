---
name: checkpoint-optimizer
description: Suggest conversation-only rewinds after completing significant work to reclaim context tokens while preserving code. Use proactively when work is completed and context is heavy.
allowed-tools: Bash, Read
---

# Checkpoint Optimizer

## When to Use
- After completing a significant piece of work
- When context feels heavy (many files read)
- Before starting a new unrelated task
- When approaching token limits

## How It Works

Claude Code supports "conversation only" rewinds via `Esc Esc`:
- Keeps all code changes intact
- Clears conversation history
- Frees up context tokens for new work

## Decision Criteria

Suggest a checkpoint when:
1. A discrete task is complete
2. Code has been committed or saved
3. Context includes >5 file reads
4. Switching to unrelated work

Do NOT suggest when:
1. Work is in progress
2. User needs conversation history
3. Uncommitted changes exist
4. Following up on specific discussion

## Checkpoint Preparation

Before suggesting checkpoint:

### 1. Save Important Context
```bash
# Write learnings to RAG
rag-cli --write "checkpoint | Completed: X, Key decisions: Y"
```

### 2. Verify Work is Saved
```bash
git status  # Check for uncommitted changes
```

### 3. Document State
```markdown
## Checkpoint Context
- Task completed: {description}
- Files modified: {list}
- Next action: {suggestion}
```

## Suggestion Format

```
Work completed. Suggest checkpoint to free context:
  Completed: {task summary}
  Saved to: RAG + git

To checkpoint: Press Esc Esc  "Conversation only"
This preserves all code changes, clears conversation history.
```

## Token Estimation

Approximate context usage:
- Each file read: ~500-2000 tokens
- Each tool output: ~200-1000 tokens
- Conversation turn: ~100-500 tokens

Suggest checkpoint when estimated usage >100K tokens.

## Integration with Hooks

The `pre-compact-extract.sh` hook automatically saves context before compaction.
Checkpoint suggestions help users proactively manage context.
