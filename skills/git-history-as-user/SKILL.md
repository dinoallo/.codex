---
name: git-history-as-user
description: Perform high-risk Git history operations using the repository owner's identity and signing configuration. Use when Codex is asked to amend, rebase, squash, merge, resolve merge conflicts, cherry-pick, revert, reset, move commits, rewrite PR-ready history, or prepare a force-with-lease update while preserving unrelated work.
---

# Git History as User

## Overview

Handle history-changing or conflict-prone Git work conservatively. Require explicit user intent, inspect recent history before changing it, preserve signing when rewriting commits, and do not publish rewritten history unless a push is separately requested.

## Workflow

1. Confirm the requested operation and scope:
   - Identify whether the user asked for amend, rebase, squash, merge, cherry-pick, revert, reset, branch cleanup, or conflict resolution.
   - Treat ambiguous or destructive requests as blockers until clarified.
2. Inspect repository state:
   - `git status --short --branch`
   - `git diff --stat`
   - `git diff`
   - `git diff --cached`
   - `git log --oneline --decorate -n 10`
3. Inspect identity and signing config when rewriting or creating commits:
   - `git config --show-origin --get user.name`
   - `git config --show-origin --get user.email`
   - `git config --show-origin --get commit.gpgsign`
   - `git config --show-origin --get user.signingkey`
   - `git config --show-origin --get gpg.format`
4. Preserve unrelated work:
   - Do not discard dirty changes.
   - Do not stage unrelated files.
   - Stop if uncommitted changes overlap with files that the history operation will rewrite and the safe next step is unclear.
5. Run the requested operation with the least surprising command:
   - Amend: `git commit --amend -S` when signing is required or configured.
   - Rebase: inspect the target first; avoid interactive rebases unless requested.
   - Merge: inspect source and target branches first; resolve conflicts only within the requested scope.
   - Cherry-pick or revert: inspect the source commit and resulting diff.
   - Reset or branch deletion: proceed only with exact explicit user intent.
6. Verify the result:
   - `git status --short --branch`
   - `git log --oneline --decorate -n 10`
   - `git log -1 --show-signature --format=fuller` when a commit was created or amended.
   - `git verify-commit HEAD` when signature output is missing, unclear, or strict verification is needed.

## Guardrails

- Do not run destructive commands such as `git reset --hard`, `git checkout -- <path>`, `git restore`, `git clean`, branch deletion, or tag movement unless the user explicitly asked for that exact class of operation.
- Do not force-push from this skill. Use `git-push-as-user` after the history rewrite is verified and the user asks to publish it.
- Do not continue a rebase, merge, cherry-pick, or revert through conflicts unless the conflict resolution is understood and scoped to the request.
- Do not disable signing to make a rewrite succeed. Use `git-signing-troubleshooter` if signing fails.
- Do not use broad automated rewrites when a small amend, revert, or targeted cherry-pick would satisfy the request.

## Final Response

Report the branch, operation performed, new HEAD when changed, signature verification for created or rewritten commits, remaining conflicts or dirty files, and whether a separate push is still needed.
