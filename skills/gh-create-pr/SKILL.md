---
name: gh-create-pr
description: Create GitHub pull requests with gh CLI. Use when Codex is asked to open, create, raise, or prepare a GitHub PR from a local branch, including draft PRs, reviewer/label assignment, PR title/body preparation, duplicate PR checks, and post-create verification. This skill is specifically for `gh pr create` workflows, not general GitHub Actions debugging or broad Git history work.
---

# GH Create PR

## Overview

Use `gh` CLI to create a pull request from the current repository while preserving the user's branch, commits, and unrelated work. Prefer explicit, non-interactive commands so the resulting PR title, body, base branch, head branch, and metadata are reviewable.

## Workflow

1. Inspect local repository state:
   - `git status --short --branch`
   - `git branch --show-current`
   - `git remote -v`
   - Preserve unrelated dirty files. If uncommitted changes exist, state that they are not part of the PR unless the user explicitly asks to commit them first.
2. Confirm GitHub CLI access and repository context:
   - `gh auth status`
   - `gh repo view --json nameWithOwner,url,defaultBranchRef`
   - Treat missing `gh`, missing auth, permission failures, and sandbox/network failures as blockers.
   - If access fails, report the failing command, the missing GitHub capability, and the next permission step for the user, such as `gh auth login`, `gh auth refresh -s repo`, `gh auth refresh -s read:org`, org SSO authorization, or repo write access.
3. Identify the PR branch and base:
   - Use the current branch as head unless the user named another branch.
   - Use the user's requested base branch when provided.
   - Otherwise prefer `git config branch.<current>.gh-merge-base` when set, then the repository default branch from `gh repo view`.
   - Do not create a PR from the base/default branch without explicit confirmation.
4. Check whether a PR already exists for the head branch:
   - `gh pr view --json number,url,state,title,headRefName,baseRefName`
   - If an open PR exists, report it instead of creating a duplicate unless the user explicitly asks for a separate PR.
5. Confirm the branch is published before creation:
   - Inspect upstream locally with `git rev-parse --abbrev-ref --symbolic-full-name @{u}` when available.
   - Do not rely on interactive `gh pr create` prompts that may fork or push.
   - If the branch is not pushed, either ask before pushing or run an explicit user-requested push such as `git push -u origin HEAD`; then retry PR creation.
6. Prepare the title and body:
   - Derive a concise title from the branch, commits, or user request.
   - Summarize the change, verification performed, and any known risk or skipped checks.
   - Use an existing PR template if it exists and is relevant; fill required sections rather than leaving placeholders.
   - Use `--body-file <file>` for multiline bodies. A temporary file under `/tmp` is acceptable.
7. Create the PR non-interactively:
   - `gh pr create --base <base> --head <head> --title "<title>" --body-file <body-file>`
   - Add requested metadata with `--draft`, `--reviewer`, `--label`, `--assignee`, `--milestone`, or `--project`.
   - Use `--fill`, `--fill-first`, or `--fill-verbose` only when the user wants commit-derived PR text. Explicit `--title` or `--body-file` takes precedence.
   - Avoid `--web` unless the user specifically wants the browser flow.
8. Verify and report:
   - `gh pr view --json number,url,title,state,isDraft,baseRefName,headRefName`
   - Report the PR URL, base/head, draft status, and verification command.

## Guardrails

- Use `gh` CLI for GitHub PR operations; do not switch to browser or raw API workflows unless the user asks.
- Do not commit, amend, rebase, merge, or push unless the user explicitly asks for that Git operation. If those operations are needed, follow the repository's Git workflow rules first.
- Do not create duplicate PRs for the same head branch.
- Do not let `gh pr create` prompt for title/body, fork choice, or push target; pass explicit flags.
- Do not add reviewers, labels, projects, milestones, or assignees unless the user asks or the repository convention is already clear.
- If project assignment fails due to missing `project` scope, report `gh auth refresh -s project` as the required auth step instead of changing auth automatically.
- If any GitHub operation fails due to auth, OAuth scope, SAML SSO, org policy, missing repo role, fork restriction, or branch protection, stop and tell the user exactly what permission or approval is needed. Do not attempt to change credentials, refresh scopes, fork, or bypass policy unless the user explicitly asks.
- Avoid pasting secrets or sensitive internal URLs from PR templates, commit messages, or command output.

## Command Patterns

Create a regular PR:

```bash
gh pr create --base <base> --head <head> --title "<title>" --body-file <body-file>
```

Create a draft PR:

```bash
gh pr create --draft --base <base> --head <head> --title "<title>" --body-file <body-file>
```

Verify the created or existing PR:

```bash
gh pr view --json number,url,title,state,isDraft,baseRefName,headRefName
```
