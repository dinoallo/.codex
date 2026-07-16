---
name: git-workflow-as-user
description: Route Git workflows that must preserve the repository owner's identity, signing configuration, remotes, branches, and unrelated work. Use when a request spans multiple focused Git skills, when no narrower Git skill clearly applies, or when Codex needs shared Git safety rules before selecting `git-commit-as-user`, `git-push-as-user`, `git-history-as-user`, `git-tag-as-user`, or `git-signing-troubleshooter`.
---

# Git Workflow as User

## Overview

Operate Git as the user, not as the assistant. Preserve the repository's effective author, committer, signing, hooks, remotes, branches, staged state, and unrelated work.

Prefer a narrower skill when the intent is clear:

- Commit local changes: use `git-commit-as-user`.
- Push branches or refs: use `git-push-as-user`.
- Amend, rebase, merge, squash, reset, revert, cherry-pick, or otherwise alter history: use `git-history-as-user`.
- Create or verify signed tags: use `git-tag-as-user`.
- Diagnose commit or tag signing failures: use `git-signing-troubleshooter`.

Use this router for mixed requests such as "commit and push", "amend then force-with-lease push", "tag and publish a release tag", or ambiguous Git work that needs triage.

## Shared Rules

- Inspect local state before Git metadata writes:
  - `git status --short --branch`
  - `git diff --stat`
  - `git diff --cached --stat` when staged changes exist.
- Preserve unrelated user changes. Never stage, discard, reformat, or rewrite files outside the requested work.
- Use repository-local Git configuration over global configuration when both exist.
- Do not set or rewrite `user.name`, `user.email`, signing keys, signing programs, `GPG_TTY`, `SSH_AUTH_SOCK`, hooks, or global Git config unless the user explicitly asks.
- Do not use assistant, bot, noreply, placeholder, or guessed identity values.
- Treat destructive operations and history rewrites as requiring explicit user intent: `reset --hard`, `checkout -- <path>`, `restore`, `clean`, branch deletion, tag movement, rebase, amend, squash, and force-push.
- Treat remote operations as publication. Do not push, fetch, pull, or contact remotes unless the user asked for a remote action or that action is required by the selected workflow.
- If a command fails due to sandbox restrictions, rerun with the required approval rather than changing the Git workflow.

## Routing Workflow

1. Classify the user intent into the narrowest matching Git skill.
2. If multiple skills apply, run them in a safe order:
   - Commit before push.
   - Rewrite or amend before push.
   - Tag before pushing a tag.
   - Diagnose signing before retrying a signing operation.
3. For each phase, follow the selected skill's verification and final reporting rules.
4. If a later phase becomes unsafe or ambiguous, stop and report the completed phase plus the blocker.

## Final Response

Include the branch, remaining worktree state, commit or tag hashes when created, signature verification result when applicable, checks run, and any remote publication result only when a remote action was requested.
