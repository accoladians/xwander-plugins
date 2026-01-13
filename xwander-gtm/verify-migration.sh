#!/bin/bash
# xwander-gtm Claude Code Migration Verification Script

echo "=== xwander-gtm Claude Code Migration Verification ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAIL++))
    fi
}

echo "1. File Structure"
echo "-----------------"
test -f .claude-plugin/plugin.json && check "plugin.json exists" || check "plugin.json exists"
test -d commands && check "commands/ directory exists" || check "commands/ directory exists"
test -d skills/gtm-ops && check "skills/gtm-ops/ directory exists" || check "skills/gtm-ops/ directory exists"
test -d agents && check "agents/ directory exists" || check "agents/ directory exists"
test -d hooks && check "hooks/ directory exists" || check "hooks/ directory exists"
echo ""

echo "2. Commands"
echo "-----------"
test -f commands/gtm-publish.md && check "gtm-publish.md" || check "gtm-publish.md"
test -f commands/gtm-list-tags.md && check "gtm-list-tags.md" || check "gtm-list-tags.md"
test -f commands/gtm-enable-ec.md && check "gtm-enable-ec.md" || check "gtm-enable-ec.md"
test -f commands/gtm-sync.md && check "gtm-sync.md" || check "gtm-sync.md"
echo ""

echo "3. Skills"
echo "---------"
test -f skills/gtm-ops/SKILL.md && check "gtm-ops/SKILL.md" || check "gtm-ops/SKILL.md"
echo ""

echo "4. Agents"
echo "---------"
test -f agents/gtm-publisher.md && check "gtm-publisher.md" || check "gtm-publisher.md"
test -f agents/ec-auditor.md && check "ec-auditor.md" || check "ec-auditor.md"
echo ""

echo "5. Hooks"
echo "--------"
test -f hooks/hooks.json && check "hooks.json" || check "hooks.json"
echo ""

echo "6. JSON Validation"
echo "------------------"
cat .claude-plugin/plugin.json | jq . > /dev/null 2>&1 && check "plugin.json valid JSON" || check "plugin.json valid JSON"
cat hooks/hooks.json | jq . > /dev/null 2>&1 && check "hooks.json valid JSON" || check "hooks.json valid JSON"
echo ""

echo "7. Python Integration"
echo "---------------------"
python3 -c "from xwander_gtm import GTMClient, TagManager, WorkspaceManager, Publisher" 2>/dev/null && check "Python imports work" || check "Python imports work"
python3 -c "from xwander_gtm import GTMClient; GTMClient()" 2>/dev/null && check "GTMClient() initialization (unified auth)" || check "GTMClient() initialization (unified auth)"
echo ""

echo "8. Documentation"
echo "----------------"
test -f CLAUDE_CODE_MIGRATION.md && check "CLAUDE_CODE_MIGRATION.md" || check "CLAUDE_CODE_MIGRATION.md"
test -f MIGRATION_SUMMARY.md && check "MIGRATION_SUMMARY.md" || check "MIGRATION_SUMMARY.md"
echo ""

echo "=== Summary ==="
echo -e "${GREEN}PASS: $PASS${NC}"
echo -e "${RED}FAIL: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✓ Migration verification COMPLETE"
    exit 0
else
    echo "✗ Migration verification FAILED"
    exit 1
fi
