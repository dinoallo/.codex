---
name: git-push-as-user
description: Push Git branches, commits, tags, or explicit refspecs to remotes using the user's repository configuration. Use when Codex is asked to push, publish, set upstream, update a PR branch, run push dry-runs, publish tags, or diagnose push rejection while preserving branch safety and avoiding unintended remote writes.
---

# Git Push as User

## Overview

Publish Git refs only when the user asks for remote publication. Confirm the target remote and ref, inspect what will be sent, prefer dry-runs for risky pushes, and handle remote failures without rewriting history by surprise.

## Workflow

1. Inspect local state:
   - `git status --short --branch`
   - `git branch --show-current`
   - `git remote -v`
   - `git rev-parse --abbrev-ref --symbolic-full-name @{u}` when an upstream may exist.
2. Determine the exact target:
   - Use the user's explicit remote, branch, tag, or refspec when provided.
   - Use plain `git push` only when the current branch tracks the intended upstream and the ahead commits are exactly the intended commits.
   - Ask before guessing when the branch has no upstream or multiple plausible remotes.
3. Inspect the commits or refs to publish:
   - `git log --oneline --decorate @{u}..HEAD` when an upstream exists.
   - `git show --stat --oneline --decorate --no-renames <tag>` before publishing a tag.
   - Use local refs only when they already exist; do not fetch just to inspect unless remote contact is requested or necessary.
4. Run a dry-run before first-time branch publication, explicit refspec pushes, tag pushes, force-with-lease pushes, or pushes to high-risk remotes:
   - `git push --dry-run <remote> <refspec>`
5. Push after dry-run confirms the intended target, or when the push is routine and unambiguous:
   - `git push`
   - `git push -u <remote> HEAD`
   - `git push <remote> <branch>`
   - `git push <remote> <tag>`
   - `git push --force-with-lease <remote> <branch>` only after explicit user intent for rewritten history.
6. Verify and report:
   - `git status --short --branch`
   - Report the remote, refspec, dry-run result when used, actual push result, and any remaining local ahead/behind state.

## Remote Access and Escalation

Remote commands contact the network and may require sandbox approval. After local preflight confirms the exact target, run the first remote-contacting command with escalation rather than intentionally provoking a sandbox network failure.

Name the operation in the approval request: dry-run or actual push, remote, branch/tag/refspec, and whether force-with-lease is involved.

For GitHub remotes, if dry-run or push fails due to authentication, token scope, SAML SSO, missing repository role, branch protection, required reviews/checks, deploy key restrictions, or protected tag rules, report the failing command and the exact permission or maintainer action needed. Do not change credentials, reconfigure remotes, bypass protections, or force-push unless the user explicitly asks.

`gh-auth-profile` applies to `gh` CLI API commands, not to Git transport by default. Do not assume `GH_TOKEN` will authenticate SSH pushes. If a push uses HTTPS token credentials, treat that as Git credential-helper or remote configuration work rather than silently switching the `gh` profile.

## Guardrails

- Do not push unless the user asked to push, publish, update a PR branch, or perform an equivalent remote operation.
- Do not use `--force`; use `--force-with-lease` only when the user explicitly asked for a rewrite that requires it.
- Do not use broad refspecs such as `--all`, `--mirror`, or `--tags` unless the user explicitly asked for that publication scope.
- Do not push known-failing commits unless the user explicitly asks to publish anyway and the final response calls out failed or skipped checks.
- If a push is rejected, do not automatically pull, merge, rebase, or force-push. Inspect and report the rejection cause, then proceed only when the next step is clearly requested.
- Never push to production, deployment, release, or protected branches unless the user explicitly requested that target.

## Final Response

Report the branch, pushed remote/refspec, dry-run and push status, remaining worktree state, and whether the local branch is still ahead or behind.
