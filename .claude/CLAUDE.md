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
