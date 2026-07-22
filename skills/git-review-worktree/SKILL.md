---
name: git-review-worktree
description: Prepare isolated Git worktrees for code review setup. Use when Codex needs to create a local review workspace for a user-provided commit, branch, ref, or GitHub pull request without disturbing the user's current checkout. Supports ordinary Git review refs and GitHub PR review setup with gh CLI, local remotes, and detached worktrees. Do not use for performing the actual code review, posting GitHub review comments, creating pull requests, pushing branches, or rewriting Git history.
---

# Git Review Worktree

## Overview

Prepare a separate worktree for review work while preserving the user's current checkout and unrelated local changes. Prefer detached worktrees under `.worktrees/` and use only repositories the user has provided or explicitly approved.

## Core Rules

- Require a local repository path from the user or confidently infer it from the current working directory.
- If no local repository is available, stop and ask the user for a repo path or explicit permission to clone. Do not clone automatically.
- Do not switch branches, reset, clean, merge, rebase, commit, push, or edit the user's primary worktree.
- Create review worktrees detached by default to avoid branch name collisions and "already checked out" failures.
- Place default review worktrees under `<repo>/.worktrees/` and add `.worktrees/` to `<repo>/.git/info/exclude`, not project `.gitignore`.
- Treat network, GitHub auth, missing `gh`, missing remotes, and inaccessible PRs as blockers. Report the failing command and the user action needed.

## Preferred Tool

Use `scripts/setup_review_worktree.py` for repeatable setup:

```bash
python3 <skill-dir>/scripts/setup_review_worktree.py ref --repo-path <repo> --ref <commit-or-branch>
```

```bash
python3 <skill-dir>/scripts/setup_review_worktree.py pr --repo-path <repo> --pr <number-or-url> --github-repo <OWNER/REPO> --remote <remote>
```

Use `--dry-run` first when the target ref, remote, or path is uncertain; it still performs read-only local Git validation but skips writes, fetches, and `gh` network access. Use `--worktree-path <path>` only when the user requested a specific location.

## Ordinary Ref Review

1. Confirm the repo path:
   - Use the user's supplied local path when provided.
   - Otherwise use the current working directory only if `git rev-parse --show-toplevel` succeeds.
   - If neither works, ask for a local repo path or clone approval.
2. Resolve the requested commit, branch, tag, or ref with `git rev-parse --verify <ref>^{commit}`.
3. Create a detached worktree for that commit:
   - Default path: `<repo>/.worktrees/review-<ref-slug>-<short-sha>`.
   - Command pattern: `git -C <repo> worktree add --detach <path> <sha>`.
4. Report the worktree path and resolved commit.

## GitHub PR Review

1. Require or infer all required inputs:
   - Local repo path: user-provided or current Git repository.
   - PR: number or GitHub PR URL from the user.
   - GitHub repo: explicit `<OWNER/REPO>` or inferred from the selected remote URL.
   - Remote: user-provided remote name, otherwise `origin`.
2. Use repository-specific GitHub auth if needed:
   - If `gh-auth-profile` applies for the target repo, read that skill and run the setup command under the selected profile environment.
   - Do not run `gh auth switch` or change global gh state.
3. Confirm PR access with `gh pr view <pr> -R <OWNER/REPO> --json number,url,title,headRefName,headRefOid,baseRefName,isCrossRepository`.
4. Fetch the PR head from the chosen remote into a local review ref:
   - Command pattern: `git -C <repo> fetch <remote> refs/pull/<pr>/head:refs/review-worktree/pr-<pr>`.
   - This GitHub pull ref works for typical fork PRs against the base repository.
5. Create a detached worktree at `<repo>/.worktrees/pr-<pr>-<head-slug>-<short-sha>`.
6. Report the PR URL, title, base/head refs, worktree path, and resolved commit.

## Manual Fallback

Use manual commands only when the script is unsuitable for the local environment:

```bash
git -C <repo> rev-parse --show-toplevel
git -C <repo> rev-parse --verify <ref>^{commit}
git -C <repo> worktree add --detach <repo>/.worktrees/review-<slug> <sha>
```

For PRs:

```bash
gh pr view <pr> -R <OWNER/REPO> --json number,url,title,headRefName,headRefOid,baseRefName,isCrossRepository
git -C <repo> fetch <remote> refs/pull/<pr>/head:refs/review-worktree/pr-<pr>
git -C <repo> worktree add --detach <repo>/.worktrees/pr-<pr>-<slug> refs/review-worktree/pr-<pr>
```

## Cleanup Guidance

Do not remove worktrees unless the user asks. If asked, inspect first with `git -C <repo> worktree list`, then remove only the named review worktree with `git -C <repo> worktree remove <path>`.
