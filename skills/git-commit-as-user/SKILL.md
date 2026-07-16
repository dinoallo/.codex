---
name: git-commit-as-user
description: Create Git commits using the repository owner's identity and signing configuration. Use when Codex is asked to inspect changes for a commit, stage selected files, write a commit message, create a signed or normal commit, verify commit signatures, or commit local work while preserving unrelated changes.
---

# Git Commit as User

## Overview

Create commits as the repository owner. Stage only intended changes, preserve existing identity and signing configuration, check for secrets, create one coherent commit, and verify the result.

## Workflow

1. Inspect repository context:
   - `git status --short --branch`
   - `git diff --stat -- <paths>` for targeted commits, or `git diff --stat` for the intended dirty worktree.
   - `git diff -- <paths>` for content that has not already been reviewed.
   - `git diff --cached --stat` when staged changes already exist.
2. Inspect effective identity and signing config without changing it when not already known:
   - `git config --show-origin --get user.name`
   - `git config --show-origin --get user.email`
   - `git config --show-origin --get commit.gpgsign`
   - `git config --show-origin --get user.signingkey`
3. Stage only intended paths:
   - Prefer `git add -- <paths>`.
   - Use `git add -p -- <paths>` only when partial staging is needed and the hunks are clear.
   - Never stage unrelated dirty files.
4. Review the staged result:
   - `git diff --cached --stat`
   - `git diff --cached --name-status`
   - `git diff --cached -- <paths>` when staged content was not already reviewed or partial staging was used.
5. Run the staged privacy and secret check:
   - Inspect staged filenames for `.env`, `.npmrc`, `.pypirc`, `.netrc`, kubeconfig files, private keys, certificates, and filenames containing `secret`, `credential`, `token`, `password`, or `private`.
   - Inspect added lines with `git diff --cached --unified=0 --no-color`.
   - Block likely real secrets, private keys, OAuth/JWT/Bearer tokens, API keys, refresh tokens, passwords, production URLs, account IDs, and machine-specific personal data.
   - Treat placeholders such as `example.com`, `REDACTED`, `<TOKEN>`, `your-token`, `changeme`, and documented test fixtures as acceptable when clearly fake.
6. Choose the commit message:
   - Use the repository's documented convention when one exists.
   - Otherwise use Conventional Commits in English: `<type>(<scope>): <summary>` or `<type>: <summary>`.
   - Prefer `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, or `chore`.
   - Keep the subject imperative, concise, lowercase type, and without a trailing period.
7. Commit with the user's configured signing behavior:
   - Use `git commit -m "<subject>"` when `commit.gpgsign=true` or signing is not explicitly required.
   - Use `git commit -S -m "<subject>"` when the user specifically asks for a signed commit or the local workflow requires explicit signing.
8. Verify the commit:
   - `git log -1 --show-signature --format=fuller`
   - `git show --stat --oneline --decorate --no-renames HEAD`
   - Run `git verify-commit HEAD` when signature output is missing, unclear, or the user requested strict verification.

## Guardrails

- Do not invent or configure Git identity.
- Do not commit if staged changes contain likely real secrets unless the user explicitly confirms they are intentional.
- Do not commit unrelated formatting churn, generated files, lockfiles, or docs unless they are part of the requested change or repository workflow.
- Do not amend, rebase, tag, merge, push, or force-push from this skill. Use the narrower matching skill for those operations.
- If signing fails, stop and use `git-signing-troubleshooter` instead of disabling signing.

## Final Response

Report the branch, commit hash and subject, signature verification result, checks run, and remaining dirty worktree state.
