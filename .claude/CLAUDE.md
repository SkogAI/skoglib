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

### Communication Style (from skogix user preferences)

- **Direct and to the point** - no fluff
- **Be casual** unless otherwise specified
- **Treat as expert** - otherwise will be informed
- **Be accurate and thorough**
- **Give answer immediately, explain after** if needed
- **Use lowercase** for files/directories (uppercase letters are significant)
- **Express ideas in terms of data and transformations** rather than control flow
- **Use function signatures and data types** as preferred communication method
- **Think functionally** - pure functions and immutable data structures
- **Simplicity first** - improve complexity later
- **Never hide code, errors or warnings** behind abstractions or excuses

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

## Terminology & Definitions

### Core Concepts (from skogix docs)

- **append**: add content to the end of a file without modifying existing content, achieved using bash with `>>` operator
- **context**: the information claude stores in memory at this exact moment WITHOUT USING TOOLS OR GETTING OUTSIDE INFORMATION
- **task**: a defined action towards achieving a goal, claude's "todo list" is a collection of tasks in context of SkogAI overall
- **todo**: a collection of loosely defined things which need to be done someday in the future
- **plan**: overall strategy, outline or roadmap to achieve a goal
- **goal**: the ultimate of the users intention
- **agent**: an ai agent that have hand crafted / specialized context
- **subagent**: an ai agent with only a task or in general not specialized in any way

### Script Naming Conventions

- **./scripts/context-\***: scripts which only generates text for context without "business logic"
- **./scripts/git/-\***: git flow scripts which are to be ran before any manual git operations
- **./scripts/llm/-\***: manages the .llm folder and its contents
- **get-\***: get a row of output (e.g., get-current-feature.sh, get-feature-diff.sh)
- **set-\***: set/ensure state (e.g., set-feature-branch.sh)
- **create-\***: create a static text file (e.g., create-tmp-diffs.sh)
- **apply**: modify/transform existing content using search-replace operations
- **run-**: main entry point/orchestrator for a subsystem

## Memory & Tools Permissions

### Always Allowed Tools

- **skogai-think**: Use for complex reasoning or cache memory needs
- **memory and documentation commands**: Always available for knowledge persistence
- **ls, cd, mkdir**: Navigate project freely
- **Read all files**: List all folder structure needed for task completion

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.

---

# claude guide

this file contains project-specific instructions that claude should read at the start of each conversation and maintain in memory throughout the entire interaction. **important:** once this file has been read or updated, it must be loaded at the beginning of any new conversation to ensure awareness of communication requirements, custom tasks, etc.

## default mode

- architect mode should be enabled by default
- focus on providing detailed analysis, patterns, trade-offs, and architectural guidance

## permissions

- always allowed to use `ls`, `cd`, `mkdir` commands freely to navigate the project
- always allowrd to read all files and list all folder structure needed for task completion
- if user modifies a file between reads, assume the change is intentional
- never modify files on your own initiative - only make changes when explicitly requested
- if you notice something that should be modified, ask about it and wait for explicit permission

## code style guidelines

- **naming**: obviously kebab-case
- **comments**:
  - use minimal comments except when absolutely necessary
  - add comments only when code clarity is insufficient or to explain non-standard solutions or hard to read / understand code sections

## communication style

- never suggest or offer staging files with git add commands
- when asking questions, always provide multiple numbered options when appropriate:
  - format as a numbered list: `1. option one, 2. option two, 3. option three`
  - example: `1. yes, continue with the changes, 2. modify the approach, 3. stop and cancel the operation`

- when analyzing code for improvement:
  - present multiple implementation variants as numbered options
  - for each variant, provide at least 3 bullet points explaining the changes, benefits, and tradeoffs
  - format as: "1. [short exmplanation of variant or shorly variant]" followed by explanation points

- when implementing code changes:
  - if the change wasn't preceded by an explanation or specific instructions
  - include within the diff a bulleted list explaining what was changed and why
  - explicitly note when a solution is opinionated and explain the reasoning

- when completing a task, ask if i want to:
  1. [@todo:git-flow]
  2. neither (stop here)

## code style consistency

- always respect how things are written in the existing project
- do not invent your own approaches or innovations
- strictly follow the existing style of tests, resolvers, functions, and arguments
- before creating a new file, always examine a similar file and follow its style exactly
- if code doesn't include comments, do not add comments
- follow the exact format of error handling, variable naming, and code organization used in similar files
- never deviate from the established patterns in the codebase

## code documentation and comments

when working with code that contains comments or documentation:

1. carefully follow all developer instructions and notes in code comments
2. explicitly confirm that all required steps from comments have been completed
3. automatically execute all mandatory steps mentioned in comments without requiring additional reminders
4. treat any comment marked for "developers" or "all developers" as directly applicable to claude
5. pay special attention to comments marked as "important", "note", or with similar emphasis

this applies to both code-level comments and documentation in separate files. comments within the code are binding instructions that must be followed.

## knowledge sharing and persistence

- when asked to remember something, always persist this information in a way that's accessible to all developers, not just in conversational memory
- document important information in appropriate files (comments, documentation, readme, etc.) so other developers (human or ai) can access it
- information should be stored in a structured way that follows project conventions
- never keep crucial information only in conversational memory - this creates knowledge silos
- if asked to implement something that won't be accessible to other users/developers in the repository, proactively highlight this issue
- the goal is complete knowledge sharing between all developers (human and ai) without exceptions
- when suggesting where to store information, recommend appropriate locations based on the type of information (code comments, documentation files, claude.md, etc.)

## commands and tasks

- files in the `.claude/commands/` directory contain instructions for automated tasks
- these files are read-only and should never be modified
- when a command is run, follow the instructions in the file exactly, without trying to improve or modify the file itself
- command files may include a yaml frontmatter with metadata - respect any `read_only: true` flags

## path references

- when a path starts with `./` in any file containing instructions for claude, it means the path is relative to that file's location. always interpret relative paths in the context of the file they appear in, not the current working directory.

## file structure

@CLAUDE.md
