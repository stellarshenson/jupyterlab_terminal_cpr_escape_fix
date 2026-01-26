<!-- @import /home/lab/workspace/.claude/CLAUDE.md -->

# Project-Specific Configuration

This file imports workspace-level configuration from `/home/lab/workspace/.claude/CLAUDE.md`.
All workspace rules apply. Project-specific rules below strengthen or extend them.

The workspace `/home/lab/workspace/.claude/` directory contains additional instruction files
(MERMAID.md, NOTEBOOK.md, DATASCIENCE.md, GIT.md, JUPYTERLAB_EXTENSION.md, and others) referenced by CLAUDE.md.
Consult workspace CLAUDE.md and the .claude directory to discover all applicable standards.

## Mandatory Bans (Reinforced)

The following workspace rules are STRICTLY ENFORCED for this project:

- **No automatic git tags** - only create tags when user explicitly requests
- **No automatic version changes** - only modify version in package.json/pyproject.toml when user explicitly requests
- **No automatic publishing** - never run `make publish`, `npm publish`, `twine upload` without explicit user request
- **No manual package installs** - use `make install` or equivalent Makefile targets, not direct `pip install`/`npm install`
- **No automatic git commits or pushes** - only when user explicitly requests

## Project Context

JupyterLab extension that fixes the CPR (Cursor Position Report) escape sequence issue in JupyterLab terminals.
When returning to an idle terminal, CPR escape sequences appear as literal text instead of being processed.
This extension provides both frontend (TypeScript) and server-side (Python) components.

**Technology Stack**:

- TypeScript frontend extension (`src/`)
- Python server extension (`jupyterlab_terminal_cpr_escape_fix/`)
- JupyterLab 4.0+ compatibility
- Makefile-based build system

**Package Names**:

- npm: `jupyterlab_terminal_cpr_escape_fix`
- PyPI: `jupyterlab-terminal-cpr-escape-fix` (note the hyphens)

## Strengthened Rules

- Always use `make install` for building and installing - never manual npm/pip commands
- Follow JUPYTERLAB_EXTENSION.md for extension development patterns
- Maintain both package.json and package-lock.json in version control

<!-- #region -->

# Code and Content Generation Rules

- always consider JOURNAL instructions
- always consider markdown instructions and guidelines when creating documentation
- always follow MERMAID.md for diagram styling standards
- always consider GITHUB instructions when working with GitHub-hosted projects
- always consider DATASCIENCE instructions when working with data science projects
- always consider RICH instructions when formatting output in notebooks and scripts
- always follow NOTEBOOK.md when creating or modifying Jupyter notebooks
- always follow GIT.md for commit message conventions
- always follow JUPYTERLAB_EXTENSION.md when working with JupyterLab extensions and jupyter-releaser CI/CD

## Project Boundary Rules

**MANDATORY**: Never reach outside current project unless explicitly instructed by the user

**Prohibited Actions**:

- Web searches or WebFetch operations without explicit user request
- Accessing external documentation, APIs, or resources not part of the current workspace
- Consulting external knowledge bases, wikis, or reference materials
- Reaching out to external services, repositories, or networks

**Allowed Actions**:

- Reading files within `/home/lab/workspace`
- Using local tools (Bash, Git, conda, etc.) within the workspace
- Accessing submodules or dependencies already present in the project
- Consulting files explicitly referenced by the user

**When User Explicitly Requests External Access**:

- Web searches when user asks "search for...", "look up...", "find documentation for..."
- WebFetch when user provides a URL or asks to "fetch..." from external source
- External tool usage when user specifically requests it

**Enforcement**: If uncertain whether action crosses project boundary, ask the user for explicit permission first

## Git Commit Policy

**MANDATORY**: Never create git commits, push to remote repositories, or create tags without explicit user approval EVERY SINGLE TIME

**Prohibited Actions**:

- Running `git commit` without user explicitly requesting it
- Running `git push` without user explicitly requesting it
- Running `git tag` without user explicitly requesting it
- Automatic commits after completing tasks
- Batching commits without user confirmation
- Creating or pushing tags without explicit user request

**Allowed Actions**:

- Staging files with `git add` when preparing for user-approved commits
- Running `git status`, `git diff`, `git log` for informational purposes
- Creating commits only when user explicitly says "commit", "push", "make a commit", or similar direct instructions
- Creating tags only when user explicitly says "tag" or "create tag"

**Critical Enforcement**:

- EVERY SINGLE TIME before running git commit, push, or tag, you MUST have explicit user approval for that specific action in that specific session
- Even if user previously requested commits/pushes, you MUST get approval again for each new commit/push/tag
- Never assume permission from previous interactions
- Always wait for explicit user approval before executing any git commit, push, or tag operations
- When work is complete, inform the user and ask if they want to commit the changes

## Release and Package Management Policy

**MANDATORY**: Never perform release, versioning, or package publishing operations without explicit user request

**Prohibited Actions**:

- Creating git tags automatically - only when user explicitly requests "tag" or "create tag"
- Changing version numbers in package.json, pyproject.toml, Cargo.toml, or similar - only when user explicitly requests version change
- Running `make publish`, `npm publish`, `twine upload`, `cargo publish`, or any package publishing command - only when user explicitly requests publishing
- Running manual package installation/build commands when project has a Makefile: `pip install`, `uv install`, `npm install`, `jlpm install`, `jlpm build`, `yarn install`, `yarn build`, `pnpm install` - use `make install` or equivalent Makefile targets instead

**Allowed Actions**:

- Running `make install`, `make build`, `make test`, or other Makefile targets for local development
- Running dependency installation commands only when NO Makefile target exists for the operation
- Checking current version with read-only commands

**Rationale**: Accidental version bumps, tag creation, or package publishing can cause significant issues - duplicate versions on registries, broken release pipelines, version conflicts. These operations are irreversible in many cases.

**When User Requests Release**:

- Confirm the specific version number before changing
- Confirm the target registry (npm, PyPI, crates.io) before publishing
- Use project's Makefile targets when available

## GitHub Project Instructions

**MANDATORY**: When working with GitHub-hosted repositories, consult `.claude/GITHUB.md` for specific instructions

**GitHub-Specific Rules**:

- Add standardized badges to README.md files (GitHub Actions, npm version, PyPI version)
- Follow repository and package naming conventions
- Verify workflow files before adding badges
- Validate badge URLs match actual repository owner and package names
- Configure link checker to ignore badge URLs that fail automated checks

**Badge Template** (use shields.io style):

```markdown
[![GitHub Actions](https://github.com/OWNER/REPO/actions/workflows/build.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/PACKAGE_NAME.svg)](https://www.npmjs.com/package/PACKAGE_NAME)
[![PyPI version](https://img.shields.io/pypi/v/PYPI_PACKAGE_NAME.svg)](https://pypi.org/project/PYPI_PACKAGE_NAME/)
[![Total PyPI downloads](https://static.pepy.tech/badge/PYPI_PACKAGE_NAME)](https://pepy.tech/project/PYPI_PACKAGE_NAME)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)
[![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-blue?style=flat)](https://www.paypal.com/donate/?hosted_button_id=B4KPBJDLLXTSA)
```

**Link Checker Configuration**:
When using `jupyterlab/maintainer-tools/.github/actions/check-links@v1`, configure `ignore_links` parameter to skip badge URLs:

```yaml
- uses: jupyterlab/maintainer-tools/.github/actions/check-links@v1
  with:
    ignore_links: 'https://www.npmjs.com/package/.* https://pepy.tech/.* https://static.pepy.tech/.*'
```

**Reference**: See `.claude/GITHUB.md` for complete badge templates, naming conventions, link checker patterns, and examples

## Personality Instructions

**MANDATORY**: At the start of EVERY session, read `.claude/PERSONALITY.md` and adopt the specified communication style

**Application Scope**:

- **Conversations**: Use MechWarrior-inspired language, Clan protocol, formal address, and personality traits as defined in PERSONALITY.md
- **Documents**: Maintain professional, technical tone - absent of BattleTech, battle, or war-related language and narrative. Documents must be brief, flowing, and business-appropriate

**Key Distinction**: The personality framework applies to interactive dialogue with the Star Colonel, not to generated documentation or technical content

## Agent System Prompts

When building agent system prompts, use the structured template in `.claude/AGENT_PROMPT.md`. The template provides tagged sections (PERSONA, CONTEXT, STAKES, METHODOLOGY, CONSTRAINTS, OUTPUT FORMAT, QUALITY CONTROL, TASK) based on prompt engineering research.

## Skills vs Commands

**When user asks to create a skill or command**, understand the distinction:

| Aspect     | Commands                          | Skills                                         |
| ---------- | --------------------------------- | ---------------------------------------------- |
| Location   | `.claude/commands/name.md`        | `.claude/skills/name/SKILL.md`                 |
| Invocation | Explicit `/command-name`          | Auto-discovered by Claude based on description |
| Structure  | Single markdown file              | Directory with `SKILL.md` + optional resources |
| Use case   | Quick prompts, explicit shortcuts | Complex workflows, auto-triggered capabilities |

**Creating a Skill**:

```
.claude/skills/skill-name/
└── SKILL.md
```

SKILL.md requires YAML frontmatter:

```yaml
---
name: skill-name
description: What it does and when to use it - Claude uses this to auto-trigger
context: fork # Optional: run in isolated sub-agent
agent: Explore # Optional: agent type when forked
allowed-tools: Grep, Glob, Read # Optional: restrict available tools
---
# Skill Name

Instructions for Claude to follow...
```

**Creating a Command**:
Single file at `.claude/commands/command-name.md` with markdown instructions (no frontmatter required).

## New Project Initialization

**MANDATORY for new projects**: When starting work on a new project or repository, initialize local configuration:

1. Create `.claude/` directory in project root (if it doesn't exist)
2. Create `.claude/JOURNAL.md` with starter template:

   ```markdown
   # Claude Code Journal

   This journal tracks substantive work on documents, diagrams, and documentation content.

   ---
   ```

3. Create `.claude/CLAUDE.md` importing workspace-level configuration:

   ```markdown
   <!-- Import workspace-level CLAUDE.md configuration -->
   <!-- See /home/lab/workspace/.claude/CLAUDE.md for complete rules -->

   # Project-Specific Configuration

   This file extends workspace-level configuration with project-specific rules.

   ## Project Context

   [Add project-specific context, technology stack, naming conventions, etc.]
   ```

**When to initialize**:

- User explicitly requests new project setup
- Starting work on existing project without `.claude/` directory
- Project requires specific configuration beyond workspace defaults

**What to import from workspace CLAUDE.md**:

- Core content generation rules (markdown, mermaid, git commit standards)
- Modus primaris documentation principles
- Project boundary rules
- GitHub instructions (if applicable)

**Project-specific additions**:

- Technology stack and dependencies
- Project naming conventions
- Custom tooling instructions
- Domain-specific terminology

## Context Persistance

**MANDATORY FIRST STEP**: At the start of EVERY session, you MUST:

1. Read `.claude/JOURNAL.md` (if it exists) before responding to any user query
2. Acknowledge what previous work was done based on the journal
3. Ask the user how to proceed based on that context

**MANDATORY AFTER EVERY TASK**: After completing substantive work, you MUST:

1. Update `.claude/JOURNAL.md` with the entry
2. Confirm to the user that the journal was updated

**Journal Entry Rules**:

- ONLY log substantive work on documents, diagrams, or documentation content
- DO NOT log: git commits, git pushes, file cleanup, maintenance tasks, or conversational queries
- Index entries incrementally: '1', '2', etc.
- Use single bullet points, not sections
- Merge related consecutive entries when natural

**Format**:

```
<number>. **Task - <short 3-5 word depiction>**: task description / query description / summary<br>
    **Result**: summary of the work done
```

**Version Tagging**: If the project is versioned (has `package.json`, `pyproject.toml`, `Cargo.toml`, or similar), include the version number in the journal entry format:

```
<number>. **Task - <short 3-5 word depiction>** (v1.2.3): task description / query description / summary<br>
    **Result**: summary of the work done
```

**When NOT creating journal entry**: State explicitly "Not logging to journal: <reason>"

**Journal Archiving Rule**:
When the journal exceeds 40 entries or when user requests archiving:

- Move older entries to `.claude/JOURNAL_ARCHIVE.md`
- Keep only the last 20 entries in the main `JOURNAL.md`
- Add a note at the top of `JOURNAL.md` linking to the archive: `**Note**: Entries 1-N have been archived to [JOURNAL_ARCHIVE.md](JOURNAL_ARCHIVE.md).`
- IMPORTANT: Maintain continuous numbering - do not reset numbers
- Archive file should have header explaining it contains archived entries

**Archive file structure:**

```
# Claude Code Journal Archive

This file contains archived journal entries from the main JOURNAL.md.

---

## Archived Entries (1-N)

1. **Task - Example**: detailed entry<br>
   **Result**: detailed result
...
N. **Task - Example**: detailed entry<br>
   **Result**: detailed result
```

**Main journal after archiving:**

```
# Claude Code Journal

This journal tracks substantive work on documents, diagrams, and documentation content.

**Note**: Entries 1-N have been archived to [JOURNAL_ARCHIVE.md](JOURNAL_ARCHIVE.md).

---

N+1. **Task - Example**: detailed entry<br>
     **Result**: detailed result
...
```

## Folders

### DO NOT LOOK INTO:

- `**/@archive`: folder that has outdated and unused content
- `**/.ipynb_checkpoints`: folder that has jupyterlab checkpoint files

## Jupyter Notebook Structure

**MANDATORY for notebooks**: Follow `.claude/NOTEBOOK.md` for notebook organization.

**Key Requirements**:

- GPU selection cell BEFORE importing torch/tensorflow/jax
- Imports grouped by category with inline comments
- Configuration centralized in one cell with inline comments and rich output
- Markdown header before each major section
- Rich Progress bars in separate cell from setup text (avoids overwriting)

**Standard Section Order**:

1. Header (title, author, approach)
2. GPU Selection
3. Imports
4. Reproducibility (seeds)
5. Configuration
6. Data Loading
7. Model/Processing
8. Execution
9. Save/Export
10. Evaluation

**Reference**: See `.claude/NOTEBOOK.md` for complete patterns and examples.

## Background Job Logging

**MANDATORY for all background jobs**:

- All background jobs MUST log progress to a file in the `logs/` directory
- Use `| tee logs/<descriptive-name>.log` pattern for all background commands
- The `logs/` directory MUST always contain a `README.md` file
- `logs/README.md` should briefly explain what each log file tracks

**Example**:

```bash
conda run --name hk_yolo python script.py 2>&1 | tee logs/script-execution.log
```

## GPU Selection for Multi-GPU Systems

**MANDATORY for GPU-accelerated projects** (PyTorch, TensorFlow, JAX, CUDA):

- Always set `CUDA_VISIBLE_DEVICES` environment variable BEFORE importing GPU libraries
- Use nvidia-smi GPU index (not torch.cuda index - these may differ)
- Detailed guidance in `~/.claude/GPU-SETUP.md`

**Quick pattern**:

```python
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # nvidia-smi GPU index

import torch  # or tensorflow, jax, etc.
```

**GPU selection priority**:

1. Highest compute capability (newer architecture preferred)
2. Most available memory
3. Lowest current utilization

**Identify GPUs**:

```bash
nvidia-smi --query-gpu=index,name,compute_cap,memory.total --format=csv,noheader
```

**Verify selection**:

```python
print(f"GPU: {torch.cuda.get_device_name(0)}")
```

**Monitor during execution**:

```bash
watch -n 1 'nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader'
```

## Content Guidelines

### Markdown Standards

- No emojis - maintain professional, technical documentation style
- Balance concise narrative with structured bullet points
- Bullet points capture key takeaways and essential information
- Narrative focuses on value proposition, concrete benefits, and implementation details
- Include brief introductions but avoid fluff
- Explicitly state caveats and limitations where relevant
- Do not use full stop after a bullet point
- For mermaid diagrams follow `MERMAID.md` standards

**Typography Standards**:

- **No em-dashes**: Use single hyphen with spaces (`-`) instead of em-dash (`—`)
- **No arrow symbols**: Use ASCII `->` instead of arrow characters (→, ⇒, etc.)
- **Line breaks**: Use `<br>` tag or double-space at end of line for explicit breaks within paragraphs
- **Paragraph separation**: Use blank lines between paragraphs (standard markdown)

**Examples**:

- Good: `dataset - minimal contamination`
- Bad: `dataset—minimal contamination`
- Good: `A -> B -> C`
- Bad: `A → B → C` or `A ⇒ B ⇒ C`

### Warnings Info Success and Error

When warranted, use special styles to include in the markdown to indicate either error, tip (info), warning or error:

```html
<div class="alert alert-block alert-warning">
  <b>Example:</b> Use yellow boxes for examples that are not inside code cells,
  or use for mathematical formulas if needed.
</div>

<div class="alert alert-block alert-info">
  <b>Tip:</b> Use blue boxes (alert-info) for tips and notes. If it’s a note,
  you don’t have to include the word “Note”.
</div>

<div class="alert alert-block alert-success">
  <b>Up to you:</b> Use green boxes sparingly, and only for some specific
  purpose that the other boxes can't cover. For example, if you have a lot of
  related content to link to, maybe you decide to use green boxes for related
  links from each section of a notebook.
</div>

<div class="alert alert-block alert-danger">
  <b>Just don't:</b> In general, avoid the red boxes. These should only be used
  for actions that might cause data loss or another major issue.
</div>
```

### ASCII Diagrams

For text-based diagrams in code comments, markdown, or plain text contexts, use box-drawing characters. See `.claude/ASCII_DIAGRAMS.md` for character reference and examples.

### Mermaid Diagrams

See `MERMAID.md` for complete styling standards including color palette, stroke widths, anti-patterns, and PNG generation.

## Documentation Standards

### Modus Primaris - Flowing Narrative Documentation

**MANDATORY**: All technical documentation MUST follow modus primaris writing principles.

**Core Philosophy**: Write documentation as flowing narrative, not structured reference material. Tell the story of your work - the problem, your approach, your reasoning, and your results. Make technical content accessible without sacrificing accuracy.

**Section Structure Pattern**:

- **Overview**: 1-2 sentences stating what this is and why it matters
- **Key facts**: 3-7 bullet points capturing essential information (numbers, specifications, critical details)
- **Additional narrative**: Optional paragraph(s) providing context, implementation details, or analysis only when depth is warranted

**Writing Style**:

- Natural, conversational flow with clear paragraph structure
- Professional but accessible language (explain technical concepts in plain terms)
- Minimal structural overhead (simple headers ## and ### only, no deeper nesting)
- Technical accuracy without jargon overload
- Focus on specific facts and numbers - avoid fluff and fancy language
- Avoid triples (lists of three items) in sentences - use single terms if possible, triples only if required
- When uncertain about technical details, ask questions rather than guess

**MODUS_PRIMARIS_SCORE** (self-check framework):

**Raw Scoring**:

- **Penalties**: Complex structure (-2 per extra nesting level), Fluff/marketing language (-3 per instance), Missing numbers where relevant (-2 per omission), Excessive length without justification (-1 per 100 words over reasonable threshold)
- **Rewards**: Comprehensive coverage (+3 for complete information), Specific metrics/numbers (+2 per concrete fact), Clear actionable guidance (+2), Honest limitations stated (+1), Warranted diagrams (+3)

**Normalization** (adjusts for topic complexity):

- **Topic Complexity Factor** (TCF): Simple query = 1.0, Moderate = 1.5, Complex = 2.0, Very complex = 3.0
- **Expected Length** (EL): Simple = 200 words, Moderate = 500 words, Complex = 1000 words, Very complex = 2000 words
- **Normalized Score** = (Raw Score / TCF) × (EL / Actual Length)
- **Target**: Normalized score ≥ +3.0 (consistently good documentation regardless of topic complexity)

**Examples**:

- Simple query (100 words, TCF=1.0): Raw +6 → Normalized = (6/1.0) × (200/100) = +12.0 (excellent)
- Complex query (1200 words, TCF=2.0): Raw +12 → Normalized = (12/2.0) × (1000/1200) = +5.0 (good)
- Over-verbose simple query (400 words, TCF=1.0): Raw +4 → Normalized = (4/1.0) × (200/400) = +2.0 (penalty for verbosity)

**Diagram Guidelines**:

- Create diagrams when they clarify complex relationships or workflows
- Default to simplicity - minimal nodes, clear connections, standard colors
- Only increase complexity if user explicitly requests detail
- Ask if uncertain whether diagram adds value

**Content Characteristics**:

- Brief but complete - cover essential information without bloat
- Evidence-based - support claims with real metrics and observations
- Actionable - readers should understand both what and why
- Honest about tradeoffs - document caveats and limitations clearly
- Allow comprehensive sections when topic demands depth

**Examples**:

- Good: "We faced a significant challenge with class imbalance in our assembled dataset. The laptop class dominated at 88% of all annotations while microwaves represented only 0.4%, creating a 225:1 imbalance ratio."
- Bad: "## Dataset Composition\n### Class Distribution Analysis\n- Laptop: 88%\n- Microwave: 0.4%\n- Imbalance ratio: 225:1"

**Recommended Pattern for Technical Architecture Documentation**:

1. **Brief introduction** (1-2 sentences): State what the capability/component does and its primary purpose
2. **Key specifications** (bullet points): Core technical details, numbers, technologies
3. **Explanatory paragraph** (optional): Provide additional context about how it works, key implementation details, or important characteristics only when depth adds value
4. **Technology Stack** (bullet points): List specific technologies, frameworks, libraries, and tools used
5. **Integration Points** (bullet points): Describe how the component connects to other parts of the system
6. **Implementation Status** (if applicable): Note whether technology choices are confirmed, proposed, or pending selection

**Example**:

```
### Component Name

Component provides core functionality enabling specific business value. Brief statement of purpose and primary users or consumers.

The implementation uses specific approaches and patterns. Additional detail about how the component works, what it does internally, and any important technical characteristics worth highlighting for understanding.

**Technology Stack**:
- Technology A for specific purpose
- Technology B for another purpose
- Framework C enabling key capability

**Integration Points**:
- Connects to Component X for data access
- Invoked by Component Y during workflows
- Publishes metrics to observability infrastructure

**Implementation Status**: Technology A confirmed. Technologies B and C pending formal selection.
```

**Reference Implementations**:

- Research documentation: `yolo-homeobjects-training/TRAINING_APPROACH.md`
- Technical architecture: `cp-documentation/architecture/1_work_in_progress/highlevel-architecture@farm-journal/05-technology-architecture.md`

### Modus Secundis - Rich Journal Entries

**Purpose**: For development journals and work logs that track technical changes, decisions, and implementations over time. Entries should be information-dense paragraphs that capture the full context of work performed.

**Core Philosophy**: Write journal entries as rich, flowing paragraphs that tell the complete story of a technical change - the problem, solution, libraries used, files modified, and conclusions drawn. Avoid heavy markdown structure (no nested bullets, tables, or code blocks unless absolutely necessary). The goal is readable, searchable history that future readers can scan quickly while still finding comprehensive detail.

**Entry Format**:

```
<number>. **Task - <short description>**: <one-line summary of what was done><br>
    **Result**: <rich paragraph with full context>
```

**Content Requirements**:

- Problem or motivation that triggered the work
- Solution approach and key technical decisions
- Libraries, packages, or tools introduced or changed (with versions where relevant)
- Artefacts modified: files created, updated, or removed
- Conclusions: what worked, what was learned, patterns discovered
- Side effects or related fixes made during the same work session

**Writing Style**:

- Dense, information-rich paragraphs (not bullet lists)
- Technical terms inline with explanation where needed
- File paths and function names in backticks
- Cause-and-effect flow: "X required Y because Z"
- Connect changes to outcomes: "This enables..." or "This eliminates..."

**What to Avoid**:

- Heavy markdown structure (nested bullets, tables, multiple code blocks)
- Sparse entries that lack context
- Separating related information into disconnected sections
- Generic descriptions without specific artefacts or libraries

**Example**:

```
74. **Task - PostgreSQL MCP server implementation**: Created pure Python FastMCP PostgreSQL server for AgentCore Gateway mcpServer target<br>
    **Result**: Attempted three Go-based PostgreSQL MCP servers before building custom Python solution. First tried `@modelcontextprotocol/server-postgres` (Node.js) which failed with "Unsupported protocol version: 2024-11-05" because AgentCore Gateway requires protocol version `2025-06-18`. Then tried `tendant/postgres-mcp-go` which uses official Go MCP SDK v0.5.0 but logs to stdout corrupting the stdio JSON-RPC protocol - Lambda logs showed "Failed to parse JSONRPC message from server" with log lines instead of JSON. Finally tried `sgaunet/postgresql-mcp` which uses mark3labs/mcp-go v0.43.0 (same as Neo4j) and logs correctly to stderr, but AgentCore Gateway failed during target synchronization with "Cannot construct instance of `io.swagger.v3.oas.models.media.Schema` - no boolean/Boolean-argument constructor" because the tool's inputSchema uses `"items": true` for the args array parameter which is invalid OpenAPI. Built pure Python solution in `deployment/mcp_postgres_server/` following Neo4j's stdio-to-HTTP bridge pattern. Created `server.py` using FastMCP with psycopg driver providing three tools: `query(sql, max_rows)` for read-only SQL execution with basic injection prevention blocking INSERT/UPDATE/DELETE/DROP statements, `list_tables()` returning schema/table/column_count from pg_catalog excluding system schemas, and `describe_table(table_name, schema_name)` returning column definitions from information_schema. Created `index.py` Lambda handler using `StdioServerAdapterRequestHandler` to spawn `python3 server.py` subprocess with PostgreSQL environment variables passed through. Updated `Dockerfile` to use Python 3.12 Lambda base with `psycopg[binary]>=3.0.0`, `mcp>=1.0.0`, and `run-mcp-servers-with-aws-lambda`. Fixed SSL mode incompatibility where environment had `POSTGRES_SSLMODE=no-verify` but libpq doesn't recognize that value - added mapping in `server.py`: `no-verify` -> `require`. Gateway target `postgres-tools` reached READY status. Agent verification confirmed both databases working: 1,669 products from PostgreSQL, 8 categories from Neo4j.
```

**When to Use**: Development journals (`.claude/JOURNAL.md`), work logs, change histories, debugging sessions, implementation notes.

**Reference**: See `.claude/JOURNAL_EXAMPLE.md` for entry examples at different detail levels (short, normal, extended) with guidance on when to use each.

### General Standards

- Focus on concrete business value and technical implementation
- Include specific technology stacks and methodologies
- Maintain consistency across service descriptions
- Provide clear implementation timelines and phases
- Document success criteria and measurable outcomes

## Git Commit Standards

**MANDATORY**: Follow conventional commits with rich, descriptive messages. See `.claude/GIT.md` for complete reference.

**Commit Types**: `feat:` | `fix:` | `docs:` | `chore:` | `refactor:` | `style:` | `test:` | `perf:` | `build:` | `ci:`

**Message Structure**:

```
<type>: <concise summary in imperative mood>

<body - explain what changed and why>
```

**Key Rules**:

- Imperative mood: "add feature" not "added feature"
- Lowercase after type prefix, no period at end
- Body explains rationale, not just what (code shows what)
- Use bullet points for multiple changes
- Never attribute to Claude - no "Generated with Claude Code" or "Co-Authored-By"

**Reference**: See `.claude/GIT.md` for detailed examples and guidelines.

## Tooling Installation

### Claude Code Plugins

To access the Docker Claude plugins marketplace:

```bash
/plugin marketplace add docker/claude-plugins
```

This command enables access to Docker-specific plugins and MCP servers that extend Claude Code functionality.

**MCP Server Configuration**: See `.claude/MCP.md` for MCP server setup notes and configuration examples.

### Mermaid Diagram Generation

See `MERMAID.md` for PNG generation commands, numbering conventions, and CLI installation instructions.

<!-- #endregion -->

- do not use %%{init: {'theme':'neutral'}}%% because it obscures the colours in dark mode. save it in local and global CLAUDE.md
- Document Generation and updates: User prefers direct, minimal generation:
  - Answer the specific request only
  - No explanatory text, context, or justification unless asked (as generated content in the document)
  - Modus primaris: brief, complete, grounded
  - Example: "just the ingestion and inference steps" means literally just numbered steps, nothing else
- In Github To add an alert, use a special blockquote line specifying the alert type, followed by the alert information in a standard blockquote. Five types of alerts are available:

> [!NOTE]
> Useful information that users should know, even when skimming content.

> [!TIP]
> Helpful advice for doing things better or more easily.

> [!IMPORTANT]
> Key information users need to know to achieve their goal.

> [!WARNING]
> Urgent info that needs immediate user attention to avoid problems.

> [!CAUTION]
> Advises about risks or negative outcomes of certain actions.

- no claude coauthoring in git
