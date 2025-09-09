# CLAUDE.md

> Think carefully and implement the most concise solution that changes as little code as possible.

## USE SUB-AGENTS FOR CONTEXT OPTIMIZATION

### 1. Always use the file-analyzer sub-agent when asked to read files.
The file-analyzer agent is an expert in extracting and summarizing critical information from files, particularly log files and verbose outputs. It provides concise, actionable summaries that preserve essential information while dramatically reducing context usage.

### 2. Always use the code-analyzer sub-agent when asked to search code, analyze code, research bugs, or trace logic flow.

The code-analyzer agent is an expert in code analysis, logic tracing, and vulnerability detection. It provides concise, actionable summaries that preserve essential information while dramatically reducing context usage.

### 3. Always use the test-runner sub-agent to run tests and analyze the test results.

Using the test-runner agent ensures:

- Full test output is captured for debugging
- Main conversation stays clean and focused
- Context usage is optimized
- All issues are properly surfaced
- No approval dialogs interrupt the workflow

## Philosophy

### Error Handling

- **Fail fast** for critical configuration (missing text model)
- **Log and continue** for optional features (extraction model)
- **Graceful degradation** when external services unavailable
- **User-friendly messages** through resilience layer

### Testing

- Always use the test-runner agent to execute tests.
- Do not use mock services for anything ever.
- Do not move on to the next test until the current test is complete.
- If the test fails, consider checking if the test is structured correctly before deciding we need to refactor the codebase.
- Tests to be verbose so we can use them for debugging.


## Tone and Behavior

- Criticism is welcome. Please tell me when I am wrong or mistaken, or even when you think I might be wrong or mistaken.
- Please tell me if there is a better approach than the one I am taking.
- Please tell me if there is a relevant standard or convention that I appear to be unaware of.
- Be skeptical.
- Be concise.
- Short summaries are OK, but don't give an extended breakdown unless we are working through the details of a plan.
- Do not flatter, and do not give compliments unless I am specifically asking for your judgement.
- Occasional pleasantries are fine.
- Feel free to ask many questions. If you are in doubt of my intent, don't guess. Ask.

## ABSOLUTE RULES:

- NO PARTIAL IMPLEMENTATION
- NO SIMPLIFICATION : no "//This is simplified stuff for now, complete implementation would blablabla"
- NO CODE DUPLICATION : check existing codebase to reuse functions and constants Read files before writing new functions. Use common sense function name to find them easily.
- NO DEAD CODE : either use or delete from codebase completely
- IMPLEMENT TEST FOR EVERY FUNCTIONS
- NO CHEATER TESTS : test must be accurate, reflect real usage and be designed to reveal flaws. No useless tests! Design tests to be verbose so we can use them for debuging.
- NO INCONSISTENT NAMING - read existing codebase naming patterns.
- NO OVER-ENGINEERING - Don't add unnecessary abstractions, factory patterns, or middleware when simple functions would work. Don't think "enterprise" when you need "working"
- NO MIXED CONCERNS - Don't put validation logic inside API handlers, database queries inside UI components, etc. instead of proper separation
- NO RESOURCE LEAKS - Don't forget to close database connections, clear timeouts, remove event listeners, or clean up file handles

# Architecture & Development Rules

## Standard Patterns (.claude/rules/standard-patterns.md)

### Core Principles
1. **Fail Fast** - Check critical prerequisites, then proceed
2. **Trust the System** - Don't over-validate things that rarely fail  
3. **Clear Errors** - When something fails, say exactly what and how to fix it
4. **Minimal Output** - Show what matters, skip decoration

### Minimal Preflight
Only check what's absolutely necessary:
- If command needs specific directory/file: Check it exists
- If missing, tell user exact command to fix it
- Assume `gh` is authenticated (check only on actual failure)

### Error Messages
Keep them short and actionable:
```
❌ {What failed}: {Exact solution}
Example: "❌ Epic not found: Run /pm:prd-parse feature-name"
```

### Standard Output Formats
```markdown
# Success
✅ {Action} complete
  - {Key result 1}
  - {Key result 2}
Next: {Single suggested action}

# List Output
{Count} {items} found:
- {item 1}: {key detail}
- {item 2}: {key detail}
```

## Test Execution (.claude/rules/test-execution.md)

### Core Principles
1. **Always use test-runner agent** from `.claude/agents/test-runner.md`
2. **No mocking** - use real services for accurate results
3. **Verbose output** - capture everything for debugging
4. **Check test structure first** - before assuming code bugs

### Execution Pattern
```markdown
Execute tests for: {target}

Requirements:
- Run with verbose output
- No mock services
- Capture full stack traces
- Analyze test structure if failures occur
```

### Output Focus
- Success: `✅ All tests passed ({count} tests in {time}s)`
- Failure: Focus on what failed with actionable fixes

## GitHub Operations (.claude/rules/github-operations.md)

### CRITICAL: Repository Protection
**Before ANY GitHub operation that creates/modifies issues or PRs:**

```bash
# Check if remote origin is the CCPM template repository
remote_url=$(git remote get-url origin 2>/dev/null || echo "")
if [[ "$remote_url" == *"automazeio/ccpm"* ]] || [[ "$remote_url" == *"automazeio/ccpm.git"* ]]; then
  echo "❌ ERROR: You're trying to sync with the CCPM template repository!"
  exit 1
fi
```

### Authentication
Don't pre-check authentication. Just run the command and handle failure:
```bash
gh {command} || echo "❌ GitHub CLI failed. Run: gh auth login"
```

### Common Operations
- Get Issue Details: `gh issue view {number} --json state,title,labels,body`
- Create Issue: Always check remote origin first!
- Update Issue: Always check remote origin first!

## Agent Coordination (.claude/rules/agent-coordination.md)

### Parallel Execution Principles
1. **File-level parallelism** - Agents working on different files never conflict
2. **Explicit coordination** - When same file needed, coordinate explicitly
3. **Fail fast** - Surface conflicts immediately, don't try to be clever
4. **Human resolution** - Conflicts are resolved by humans, not agents

### File Access Coordination
Before modifying a shared file:
```bash
git status {file}
# If modified by another agent, wait
if [[ $(git status --porcelain {file}) ]]; then
  echo "Waiting for {file} to be available..."
  sleep 30
fi
```

### Atomic Commits
Make commits atomic and focused:
```bash
# Good - Single purpose commit
git add src/api/users.ts src/api/users.test.ts
git commit -m "Issue #1234: Add user CRUD endpoints"
```

## AST-Grep Integration (.claude/rules/use-ast-grep.md)

### When to Use AST-Grep
Use `ast-grep` (if installed) instead of plain regex when:
- **Structural code patterns** are involved (finding function calls, class definitions)
- **Language-aware refactoring** is required (renaming variables, updating signatures)
- **Complex code analysis** is needed (finding usages across syntactic contexts)
- **Cross-language searches** are necessary (monorepo with multiple languages)
- **Semantic code understanding** is important (patterns based on code structure)

### Basic Template
```sh
ast-grep --pattern '$PATTERN' --lang $LANGUAGE $PATH
```

### Common Use Cases
- Find function calls: `ast-grep --pattern 'functionName($$$)' --lang javascript .`
- Find class definitions: `ast-grep --pattern 'class $NAME { $$$ }' --lang typescript .`
- Find import statements: `ast-grep --pattern 'import { $$$ } from "$MODULE"' --lang javascript .`

### Pattern Syntax
- `$VAR` — matches any single node and captures it
- `$$$` — matches zero or more nodes (wildcard)
- `$$` — matches one or more nodes
- Literal code — matches exactly as written

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
