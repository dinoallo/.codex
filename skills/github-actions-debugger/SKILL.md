---
name: github-actions-debugger
description: Diagnose and fix GitHub Actions, CI failures, PR checks, failed workflow runs, and job log failures using gh CLI. Use when Codex is asked to inspect GitHub Actions status, read failed CI logs, explain PR check failures, repair code based on workflow results, or resolve repository auth profiles before reading GitHub Actions and PR check data.
---

# GitHub Actions Debugger

## Overview

Use `gh` CLI to inspect GitHub Actions and PR check failures before changing code. Work from failed job logs to the smallest local reproduction, then make scoped fixes and verify them.

## Workflow

1. Inspect local state first:
   - `git status --short --branch`
   - preserve unrelated user changes.
   - note the current branch and whether local changes may affect reproduction.
2. Resolve the target repository and auth profile before any `gh` command:
   - Infer the target repository from a PR URL, workflow run URL, explicit `--repo` or URL arguments, configured remote URLs from `git remote -v`, or the current branch's repository context.
   - Normalize the target to `host/owner/repo`, such as `github.com/labring/sealos`.
   - Do not use `gh auth status`, `gh repo view`, `gh pr`, `gh run`, or `gh api` to resolve the target before this auth gate.
   - If `gh-auth-profile` is available, read it and attempt to match a profile for the normalized target before any bare `gh` command.
   - Treat non-default auth as required for organization-owned repositories, fine-grained PAT workflows, GHES hosts, GitHub App installation tokens, private repositories, or when the target owner differs from the current fork or push remote owner. If required auth has no matching profile, stop and show the `gh-auth-profile` first-use or no-match prompt instead of falling back to bare `gh`.
   - If a profile matches, select it and run every `gh` command in this workflow with that profile's one-command token environment.
   - Only after confirming that no profile rule matches and non-default auth is not required may bare `gh` commands be used.
3. Confirm GitHub access and repository context with the resolved auth mode:
   - With a matched profile: `<profile-env> gh auth status`
   - With a matched profile: `<profile-env> gh repo view <owner/repo> --json nameWithOwner,url`
   - Without a matched profile, only when allowed by step 2: `gh auth status`
   - Without a matched profile, only when allowed by step 2: `gh repo view <owner/repo> --json nameWithOwner,url`
   - If access fails, report the failing command, the missing GitHub capability, and the next permission step for the user, such as `gh auth login`, `gh auth refresh -s repo`, `gh auth refresh -s workflow`, org SSO authorization, or repository Actions read access.
4. Prefer PR checks when the branch has an associated PR:
   - Run with the resolved auth mode: `gh pr view --json number,url,headRefName,headRefOid,statusCheckRollup`
   - Run with the resolved auth mode: `gh pr checks`
5. Find relevant workflow runs:
   - Run with the resolved auth mode: `gh run list --branch <branch> --limit 10 --json databaseId,status,conclusion,workflowName,displayTitle,headSha,url`
   - prefer failed or cancelled runs matching the PR head SHA or current branch head.
6. Inspect failed jobs and logs:
   - Run with the resolved auth mode: `gh run view <run-id> --json jobs`
   - Run with the resolved auth mode: `gh run view <run-id> --log-failed`
   - identify the failed command, assertion, file path, dependency, or environment assumption from the logs.
7. Reproduce locally when practical:
   - run the smallest matching lint, test, build, or script command.
   - inspect project manifests and CI workflow files only as needed to map the job command to local commands.
8. Fix the root cause:
   - make the narrowest code, test, dependency, or workflow change that addresses the logged failure.
   - avoid unrelated cleanup.
9. Verify and report:
   - rerun the local failing command or nearest meaningful check.
   - report the failed workflow/run, root cause, files changed, and verification result.

## Guardrails

- Do not infer the cause from workflow or check names alone; inspect failed logs.
- Do not rerun workflow runs unless the user asks.
- Do not push commits or update PRs unless the user asks.
- Do not install dependencies, access private systems, or use paid services without explicit user intent.
- If `gh` is unauthenticated, missing, or blocked by sandbox/network restrictions, report the blocker and the command that failed.
- Before running any bare `gh auth status`, `gh repo view`, `gh pr`, `gh run`, or `gh api`, first resolve whether a `gh-auth-profile` rule matches the target repository. If a matching profile exists, never run bare `gh`; run every command with the profile's one-command token environment.
- For organization-owned repositories, fine-grained PAT workflows, GHES hosts, GitHub App installation tokens, private repositories, or when the target owner differs from the current fork or push remote owner, treat non-default auth as required and use `gh-auth-profile` first.
- Do not use `gh auth switch` to change the active account. Use `gh-auth-profile` when repository-specific credentials are needed.
- If a GitHub command fails due to auth, OAuth scope, SAML SSO, org policy, missing repo role, Actions access, Checks access, or log visibility, stop and tell the user exactly what permission or approval is needed. Do not refresh scopes, change credentials, rerun workflows, or request elevated GitHub access unless the user explicitly asks.
- If logs point to secrets, tokens, or private URLs, avoid pasting sensitive values in the response.

## Common Commands

Use these commands only after the target/profile gate has selected the resolved auth mode. If a profile was selected, replace bare `gh` with that profile's one-command token environment plus `gh`.

```bash
gh auth status
gh repo view --json nameWithOwner,url
gh pr view --json number,url,headRefName,headRefOid,statusCheckRollup
gh pr checks
gh run list --branch <branch> --limit 10 --json databaseId,status,conclusion,workflowName,displayTitle,headSha,url
gh run view <run-id> --json jobs
gh run view <run-id> --log-failed
```
