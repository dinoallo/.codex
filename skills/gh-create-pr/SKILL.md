---
name: gh-create-pr
description: Create GitHub pull requests with gh CLI. Use when Codex is asked to open, create, raise, or prepare a GitHub PR from a local branch, including repository auth profile resolution, draft PRs, reviewer/label assignment, PR title/body preparation, body privacy review, duplicate PR checks, and post-create PR state confirmation. This skill is specifically for `gh pr create` workflows, not general GitHub Actions debugging or broad Git history work.
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
2. Resolve the target repository and auth profile before any `gh` command:
   - Infer the target repository from the user request, explicit `--repo` or URL arguments, configured remote URLs from `git remote -v`, and the intended base/head repository.
   - Normalize the target to `host/owner/repo`, such as `github.com/labring/sealos`.
   - Do not use `gh auth status`, `gh repo view`, `gh pr`, or `gh api` to resolve the target before this auth gate.
   - If `gh-auth-profile` is available, read it and attempt to match a profile for the normalized target before any bare `gh` command.
   - Treat non-default auth as required for organization-owned repositories, fine-grained PAT workflows, GHES hosts, GitHub App installation tokens, or when the target owner differs from the current fork or push remote owner. If required auth has no matching profile, stop and show the `gh-auth-profile` first-use or no-match prompt instead of falling back to bare `gh`.
   - If a profile matches, select it and run every `gh` command in this workflow with that profile's one-command token environment.
   - Only after confirming that no profile rule matches and non-default auth is not required may bare `gh` commands be used.
3. Confirm GitHub CLI access and repository context with the resolved auth mode:
   - With a matched profile: `<profile-env> gh auth status`
   - With a matched profile: `<profile-env> gh repo view <owner/repo> --json nameWithOwner,url,defaultBranchRef`
   - Without a matched profile, only when allowed by step 2: `gh auth status`
   - Without a matched profile, only when allowed by step 2: `gh repo view <owner/repo> --json nameWithOwner,url,defaultBranchRef`
   - Treat missing `gh`, missing auth, permission failures, and sandbox/network failures as blockers.
   - If access fails, report the failing command, the missing GitHub capability, and the next permission step for the user, such as `gh auth login`, `gh auth refresh -s repo`, `gh auth refresh -s read:org`, org SSO authorization, or repo write access.
4. Identify the PR branch and base:
   - Use the current branch as head unless the user named another branch.
   - Use the user's requested base branch when provided.
   - Otherwise prefer `git config branch.<current>.gh-merge-base` when set, then the repository default branch from the authenticated `gh repo view` result in step 3.
   - Do not create a PR from the base/default branch without explicit confirmation.
5. Check whether a PR already exists for the head branch:
   - Run with the resolved auth mode: `gh pr view --json number,url,state,title,headRefName,baseRefName`
   - If an open PR exists, report it instead of creating a duplicate unless the user explicitly asks for a separate PR.
6. Confirm the branch is published before creation:
   - Inspect upstream locally with `git rev-parse --abbrev-ref --symbolic-full-name @{u}` when available.
   - Do not rely on interactive `gh pr create` prompts that may fork or push.
   - If the branch is not pushed, either ask before pushing or run an explicit user-requested push such as `git push -u origin HEAD`; then retry PR creation.
7. Prepare the title and body:
   - Derive a concise title from the branch, commits, or user request.
   - By default, write a concise body that summarizes the change and any reviewer-critical context or risk.
   - Do not add a `Verification`, `Tests`, or `Checks` section by default. Include verification only when the user asks, the repository template requires it, or a failing/skipped check materially changes reviewer risk.
   - Use an existing PR template if it exists and is relevant; fill required sections rather than leaving placeholders. Keep template-required verification/test sections minimal and factual.
   - Use `--body-file <file>` for multiline bodies. A temporary file under `/tmp` is acceptable.
8. Review the PR title and body before creation:
   - Inspect the final title and body file before running `gh pr create`.
   - Do not paste issue bodies, issue comments, PR comments, logs, screenshots, CI output, chat excerpts, internal URLs, customer names, account IDs, machine-specific paths, local usernames, private repo URLs, security findings, or incident details unless the user explicitly asks and the content is safe for the target repository.
   - Prefer short references such as `Refs #123` or `Closes #123` over copied issue text.
   - Block or redact likely secrets and credentials, including private keys, certificates, tokens, OAuth/JWT/Bearer values, passwords, API keys, cloud keys, database DSNs, kubeconfigs, `.env` content, `ghp_`, `github_pat_`, and fine-grained PAT values.
   - Treat placeholders such as `<TOKEN>`, `REDACTED`, `github_pat_xxx`, `example.com`, and `your-org` as acceptable when clearly fake.
   - If the body may expose private information, stop and ask for a sanitized body instead of creating the PR.
9. Create the PR non-interactively:
   - Run with the resolved auth mode: `gh pr create --base <base> --head <head> --title "<title>" --body-file <body-file>`
   - Add requested metadata with `--draft`, `--reviewer`, `--label`, `--assignee`, `--milestone`, or `--project`.
   - Use `--fill`, `--fill-first`, or `--fill-verbose` only when the user wants commit-derived PR text. Explicit `--title` or `--body-file` takes precedence.
   - Avoid `--web` unless the user specifically wants the browser flow.
10. Confirm and report:
   - Run with the resolved auth mode: `gh pr view --json number,url,title,state,isDraft,baseRefName,headRefName`
   - Report the PR URL, base/head, draft status, and confirmation command.

## Guardrails

- Use `gh` CLI for GitHub PR operations; do not switch to browser or raw API workflows unless the user asks.
- Before running any bare `gh auth status`, `gh repo view`, `gh pr`, or `gh api`, first resolve whether a `gh-auth-profile` rule matches the target repository. If a matching profile exists, never run bare `gh`; run every command with the profile's one-command token environment.
- For organization-owned repositories, fine-grained PAT workflows, GHES hosts, GitHub App installation tokens, or when the target owner differs from the current fork or push remote owner, treat non-default auth as required and use `gh-auth-profile` first.
- Do not commit, amend, rebase, merge, or push unless the user explicitly asks for that Git operation. If those operations are needed, follow the repository's Git workflow rules first.
- Do not create duplicate PRs for the same head branch.
- Do not let `gh pr create` prompt for title/body, fork choice, or push target; pass explicit flags.
- Do not create a PR before reviewing the final title and body for secrets, private issue content, internal URLs, local paths, account identifiers, and other sensitive information.
- Do not include verification/test output in the PR body by default. Keep it out unless the user asks, the repository template requires it, or omitted/failing checks materially affect reviewer risk.
- Do not use `gh auth switch` to change the active account. Use `gh-auth-profile` when repository-specific credentials are needed.
- Do not add reviewers, labels, projects, milestones, or assignees unless the user asks or the repository convention is already clear.
- If project assignment fails due to missing `project` scope, report `gh auth refresh -s project` as the required auth step instead of changing auth automatically.
- If any GitHub operation fails due to auth, OAuth scope, SAML SSO, org policy, missing repo role, fork restriction, or branch protection, stop and tell the user exactly what permission or approval is needed. Do not attempt to change credentials, refresh scopes, fork, or bypass policy unless the user explicitly asks.
- Avoid pasting secrets or sensitive internal URLs from PR templates, commit messages, or command output.

## Command Patterns

Use these patterns only after the target/profile gate has selected the resolved auth mode. If a profile was selected, replace bare `gh` with that profile's one-command token environment plus `gh`.

Create a regular PR:

```bash
gh pr create --base <base> --head <head> --title "<title>" --body-file <body-file>
```

Create a draft PR:

```bash
gh pr create --draft --base <base> --head <head> --title "<title>" --body-file <body-file>
```

Confirm the created or existing PR:

```bash
gh pr view --json number,url,title,state,isDraft,baseRefName,headRefName
```
