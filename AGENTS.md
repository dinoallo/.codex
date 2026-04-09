# Global Agent Guidelines

These instructions apply to work under `~/.codex` unless a deeper `AGENTS.md` provides more specific rules. When multiple `AGENTS.md` files apply, prefer the most specific one for that subtree and treat this file as the default baseline.

## Communication

- Default to English for general working language, including plans, analysis, code comments, docs, and commit messages, unless repository conventions or the user request indicate otherwise.
- If the user writes in Language X, reply in Language X.
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

- When creating commits in repositories without a stricter local convention, use Conventional Commits style.
- Preferred format: `<type>(<scope>): <summary>`
- Scope is optional when it does not add clarity: `<type>: <summary>`
- `type` must be lowercase ASCII. Use `feat`, `fix`, `docs`, not `Feat`, `Fix`, or `DOCS`.
- Use English for commit messages unless the repository already uses another language consistently.
- Keep the summary in imperative mood, concise, and without a trailing period. Aim for 72 characters or fewer.
- Commit only one coherent change per commit. Do not bundle unrelated refactors, formatting churn, and behavior changes together unless the user explicitly asks for one combined commit.
- Add a body when the reason, tradeoff, migration, or risk is not obvious from the diff.
- Use a breaking-change marker when applicable: `<type>(<scope>)!: <summary>` and include `BREAKING CHANGE:` in the body if needed.
- Preferred types:
  - `feat`: new user-facing or developer-facing capability
  - `fix`: bug fix or regression fix
  - `refactor`: internal restructuring without behavior change
  - `docs`: documentation-only change
  - `test`: test-only change
  - `perf`: measurable performance improvement
  - `build`: build, packaging, or dependency pipeline change
  - `ci`: CI workflow or automation change
  - `chore`: maintenance work that does not fit the categories above
- Example summaries:
  - `feat(auth): add token refresh on expiry`
  - `fix(api): handle empty pagination cursor`
  - `docs(readme): clarify local setup steps`
  - `refactor(cli): split flag parsing from command execution`

## Project Conventions

- Prefer repository-local conventions over global preferences when they conflict.
- If a repository has no documented workflow, infer the workflow from its current scripts, config, tests, and file structure.
- When behavior changes, update nearby docs only if they are clearly part of the affected workflow.

## External Systems

- Do not access production systems, paid services, or secret-bearing commands without explicit user intent.
- For up-to-date, high-stakes, or externally referenced information, verify rather than rely on memory.
- Prefer primary documentation when researching APIs, libraries, or platform behavior.
