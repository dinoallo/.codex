# Global Agent Guidelines

These instructions apply to work under `~/.codex` unless a deeper `AGENTS.md` provides more specific rules. When multiple `AGENTS.md` files apply, prefer the most specific one for that subtree and treat this file as the default baseline.

## Communication

- Default to English for project artifacts and general working language, including plans, analysis, code comments, docs, and commit messages, unless repository conventions explicitly require another language.
- If the user writes in Language X, reply in Language X.
- Even when replying in Language X, keep project artifacts in English by default. For documentation files, keep the primary document in English and add a companion translation in Language X when documentation is produced for that user. Apply this rule unless the matched skill includes a more specific language or documentation convention.
- Keep final responses short and outcome-focused. Include verification status and blockers when relevant.
- Match the repository's existing language for user-facing copy unless asked otherwise.
- State assumptions explicitly when they affect implementation or verification.

## Working Style

- Before starting any non-trivial implementation, present a short plan first. The plan should state the intended change, the approach, and the expected verification.
- For trivial one-step tasks, keep the plan to one sentence rather than skipping context entirely.
- Read the nearest relevant `AGENTS.md`, `README`, and project manifests before making non-trivial changes.
- Inspect existing code and conventions before proposing refactors or introducing new patterns.
- Prefer small, targeted changes that solve the requested problem without unrelated cleanup.
- Ask questions only when a risky assumption cannot be validated from local context.
- For reviews, prioritize bugs, regressions, edge cases, and missing tests over style commentary.

## Editing Rules

- Preserve unrelated user changes. Never revert work you did not create unless explicitly asked.
- Do not use destructive commands such as `git reset --hard`, `git checkout --`, or broad `rm -rf` without explicit approval.
- Prefer `rg`/`rg --files` for search.
- Follow existing formatter, linter, and file layout conventions in each project.
- Use ASCII by default when editing unless the file already relies on Unicode or the task benefits from it.
- Add brief comments only where the logic is genuinely non-obvious.

## Verification

- Run the smallest meaningful checks that validate the change.
- Prefer targeted tests before full-suite runs unless the change is broad or the repo requires a full gate.
- If you cannot run verification, say so clearly and explain why.
- When reporting verification, mention the command or check that was run.

## Git And Change Safety

- Do not create commits, rewrite history, switch branches, or push unless the user asks for it.
- Keep commits scoped to the requested change.
- Treat the worktree as potentially shared with the user or other agents; avoid cross-cutting state changes.
- Ignore unrelated dirty files unless they block the requested work.

## Git Commit Format

- Use the repository's documented commit message convention when one exists.
- When creating commits in repositories without a stricter local convention, use the fallback convention in the `git-workflow-as-user` skill.

## Project Conventions

- Prefer repository-local conventions over global preferences when they conflict.
- For third-party Codex skill installs or updates under `~/.codex`, including requests that provide `npx skills add ...`, use the `third-party-skill-vendor` skill and the `skills/third-party.toml` plus `scripts/skill-vendor.py` workflow instead of treating an external installer as final state.
- If a repository has no documented workflow, infer the workflow from its current scripts, config, tests, and file structure.
- When behavior changes, update nearby docs only if they are clearly part of the affected workflow.

## External Systems

- Do not access production systems, paid services, or secret-bearing commands without explicit user intent.
- For up-to-date, high-stakes, or externally referenced information, verify rather than rely on memory.
- Prefer primary documentation when researching APIs, libraries, or platform behavior.
