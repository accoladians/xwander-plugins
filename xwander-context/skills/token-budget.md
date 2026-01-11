---
name: token-budget
description: Monitor and optimize token usage. Use when context feels heavy, approaching limits, or when planning large operations that may trigger compaction.
allowed-tools: Bash, Read
---

# Token Budget Management

## When to Use
- Context feels heavy (many files read)
- Planning large operations
- Before reading large files
- Optimizing agent delegation

## Token Estimation Guide

### Approximate Costs
| Content Type | Tokens (approx) |
|--------------|-----------------|
| File read (small) | 500-1000 |
| File read (large) | 2000-5000 |
| Tool output | 200-1000 |
| Conversation turn | 100-500 |
| Code block | 50-300 |
| JSON output | 100-500 |

### Context Limits
- Opus 4.5: ~200K tokens
- Sonnet: ~200K tokens
- Haiku: ~200K tokens

Warning threshold: ~150K tokens

## Optimization Strategies

### 1. Batch Tool Calls
Bad:
```
Read file1
Read file2
Read file3
```

Good:
```
Read file1, file2, file3 (parallel)
```

### 2. Use Grep/Glob Over Sequential Reads
Bad:
```
Read all files in directory
Search for pattern manually
```

Good:
```
Grep pattern across directory
Read only matching files
```

### 3. Delegate Large Outputs
Bad:
```
git log (1000+ lines)
```

Good:
```
Task(subagent_type="github-coach", prompt="summarize recent commits")
```

### 4. Cache Large Files
```bash
# Copy large file to /tmp for multiple reads
cp /srv/large-file.json /tmp/
# Read from /tmp
```

### 5. Selective Reading
```bash
# Read only relevant section
Read file_path limit=50 offset=100
```

## When to Checkpoint

Consider checkpoint when:
- Read >10 files in session
- Tool outputs >20 calls
- Switching task domains
- Work is complete and committed

## Delegation Criteria

Delegate to sub-agent when:
- Output will be >1000 lines
- Task requires multiple tool rounds
- Independent analysis needed
- Specialized domain (ads, analytics)

Sub-agent options:
- `haiku-agent`: Quick, cheap tasks
- `sonnet-agent`: Balanced tasks
- `gemini-agent`: Large context (1M+)
- `codex-agent`: Code generation

## Monitoring

Check session state:
```bash
ls -la /mnt/xwander-ai/knowledge/session-summaries/latest-*.md
```

Check transcript size (if available):
```bash
wc -l /path/to/transcript.jsonl
```

## Output Format
```
Token budget check
  Estimated usage: ~{X}K tokens
  Status: OK / WARNING / CRITICAL
  Recommendation: {action}
```
