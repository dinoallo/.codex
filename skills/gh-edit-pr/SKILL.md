---
name: gh-edit-pr
description: Edit existing GitHub pull requests with gh CLI. Use when Codex is asked to update, modify, retitle, rewrite, annotate, mark ready/draft, close, reopen, relabel, assign, change reviewers, change milestone/project, or change the base branch of an existing PR. This skill is for `gh pr edit`, `gh pr ready`, `gh pr comment`, `gh pr close`, and `gh pr reopen` workflows, not creating new PRs, merging PRs, debugging Actions, or rewriting Git history.
---

# GH Edit PR

## Overview

Use `gh` CLI to update an existing pull request without changing local commits, branches, or unrelated work. Prefer explicit, non-interactive commands and verify the PR state before and after each modification.

## Workflow

1. Identify the target PR:
   - Prefer a user-provided PR number, URL, or branch selector.
   - If no selector is provided, use the PR for the current branch only when that is unambiguous.
   - Inspect local context with `git status --short --branch` and `git branch --show-current` when relying on the current branch.
2. Confirm GitHub CLI access and repository context:
   - If the repository or organization may need a non-default GitHub identity, token, SSO authorization, GHES host, or GitHub App installation token, use `gh-auth-profile` to select the profile first.
   - `gh auth status`
   - `gh repo view --json nameWithOwner,url,defaultBranchRef`
   - When a profile is selected, run every `gh` command in this workflow with that profile's one-command token environment.
   - Treat missing `gh`, missing auth, permission failures, and sandbox/network failures as blockers.
   - If access fails, report the failing command, the missing GitHub capability, and the next permission step for the user, such as `gh auth login`, `gh auth refresh -s repo`, `gh auth refresh -s read:org`, org SSO authorization, or repo write access.
3. Snapshot the PR before editing:
   - `gh pr view <selector> --json number,url,title,state,isDraft,baseRefName,headRefName,body,labels,assignees,reviewRequests,milestone,projectItems`
   - Use this to confirm the target, avoid editing the wrong PR, and compare the result.
4. Choose the smallest command for the requested change:
   - Use `gh pr edit` for title, body, base branch, labels, assignees, reviewers, milestone, and projects.
   - Use `gh pr ready` to mark ready for review.
   - Use `gh pr ready --undo` to convert back to draft.
   - Use `gh pr comment` to add or update comments.
   - Use `gh pr close` or `gh pr reopen` only when the user explicitly asks for that state change.
5. Prepare multiline text safely:
   - Use `--body-file <file>` for PR body edits and `gh pr comment --body-file <file>` for multiline comments.
   - A temporary file under `/tmp` is acceptable.
   - Preserve meaningful PR template sections unless the user asks to replace the body wholesale.
6. Run the edit non-interactively:
   - Pass explicit flags for every requested change.
   - Avoid `--web`, `--editor`, and interactive prompts unless the user asks for the browser or editor flow.
   - Combine compatible `gh pr edit` flags in one command when that is clear and reviewable.
7. Verify and report:
   - `gh pr view <selector> --json number,url,title,state,isDraft,baseRefName,headRefName,body,labels,assignees,reviewRequests,milestone,projectItems`
   - Report the PR URL, the fields changed, and the verification command.

## Guardrails

- Use `gh` CLI for PR edits; do not switch to browser or raw API workflows unless the user asks.
- Do not create a new PR. Use `gh-create-pr` for creation workflows.
- Do not merge PRs from this skill.
- Do not commit, amend, rebase, push, delete branches, or rewrite Git history unless the user explicitly asks for that separate Git operation.
- Do not change the PR base branch, close a PR, reopen a PR, convert ready/draft state, or delete a branch unless the user explicitly requested that specific state change.
- Do not use `gh auth switch` to change the active account. Use `gh-auth-profile` when repository-specific credentials are needed.
- Do not add or remove reviewers, labels, projects, milestones, or assignees unless the user asks or the repository convention is already clear.
- If project edits fail due to missing `project` scope, report `gh auth refresh -s project` as the required auth step instead of changing auth automatically.
- If any GitHub operation fails due to auth, OAuth scope, SAML SSO, org policy, missing repo role, review/team visibility, branch protection, or project permissions, stop and tell the user exactly what permission or approval is needed. Do not attempt to change credentials, refresh scopes, or bypass policy unless the user explicitly asks.
- Avoid pasting secrets or sensitive internal URLs from PR bodies, templates, comments, or command output.

## Command Patterns

Edit title and body:

```bash
gh pr edit <selector> --title "<title>" --body-file <body-file>
```

Change labels, reviewers, and assignees:

```bash
gh pr edit <selector> --add-label "bug,help wanted" --remove-label "needs-triage"
gh pr edit <selector> --add-reviewer user-or-team --remove-reviewer old-user
gh pr edit <selector> --add-assignee "@me" --remove-assignee old-user
```

Change base branch:

```bash
gh pr edit <selector> --base <branch>
```

Change draft or ready state:

```bash
gh pr ready <selector>
gh pr ready <selector> --undo
```

Add or update a comment:

```bash
gh pr comment <selector> --body-file <comment-file>
gh pr comment <selector> --edit-last --body-file <comment-file>
```

Close or reopen only when explicitly requested:

```bash
gh pr close <selector> --comment "<comment>"
gh pr reopen <selector> --comment "<comment>"
```

Verify before and after:

```bash
gh pr view <selector> --json number,url,title,state,isDraft,baseRefName,headRefName,body,labels,assignees,reviewRequests,milestone,projectItems
```
