---
name: context-externalization
description: Automatically save important context to RAG before it's compacted. Use when discussing important decisions, learnings, configurations, or discoveries that should persist beyond this session.
allowed-tools: Bash, Write, mcp__rag-mcp__write_knowledge
---

# Context Externalization

## When to Use
- Important decisions made
- New learnings discovered
- Configuration patterns identified
- Troubleshooting solutions found
- Architecture decisions documented

## What to Externalize

### High Value (Always Save)
- Architectural decisions and rationale
- Security configurations
- API patterns that work
- Debugging solutions
- Integration patterns

### Medium Value (Consider Saving)
- Code patterns used successfully
- Configuration examples
- Workflow optimizations
- Tool usage tips

### Low Value (Skip)
- Temporary debug output
- One-time commands
- Conversation about preferences
- Trivial file reads

## Externalization Methods

### Quick Save (CLI)
```bash
rag-cli --write "topic | content"
```

### Structured Save (MCP)
```
mcp__rag-mcp__write_knowledge(
  content="# Title\n\nContent...",
  filename="descriptive-name.md",
  category="system"
)
```

### Category Selection

| Content Type | Category |
|--------------|----------|
| Infrastructure/nginx | `system` |
| Cloudflare/DNS | `cloudflare` |
| Business logic | `erp` |
| Session context | `worklogs` |
| AI tool config | `ai-tools` |

## Document Templates

### Decision Record
```markdown
# Decision: {Title}
**Date**: {timestamp}
**Context**: {situation}

## Options Considered
1. Option A: {description}
2. Option B: {description}

## Decision
Chose Option {X} because {rationale}

## Consequences
- {consequence 1}
- {consequence 2}
```

### Solution Record
```markdown
# Solution: {Problem Title}
**Date**: {timestamp}

## Problem
{description}

## Solution
{steps or code}

## Why It Works
{explanation}
```

## Automatic Triggers

The pre-compact hook automatically extracts:
- Recent files modified
- Tool usage patterns
- Session metadata

Manual externalization captures:
- Decisions and rationale
- Learnings and insights
- Patterns discovered

## Output Format
```
Context externalized
  Topic: {topic}
  Category: {category}
  Path: {path}
```
