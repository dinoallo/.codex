---
name: github-actions-debugger
description: Diagnose and fix GitHub Actions, CI failures, PR checks, failed workflow runs, and job log failures using gh CLI. Use when Codex is asked to inspect GitHub Actions status, read failed CI logs, explain PR check failures, or repair code based on workflow results.
---

# GitHub Actions Debugger

## Overview

Use `gh` CLI to inspect GitHub Actions and PR check failures before changing code. Work from failed job logs to the smallest local reproduction, then make scoped fixes and verify them.

## Workflow

1. Inspect local state first:
   - `git status --short --branch`
   - preserve unrelated user changes.
   - note the current branch and whether local changes may affect reproduction.
2. Confirm GitHub access and repository context:
   - If the repository or organization may need a non-default GitHub identity, token, SSO authorization, GHES host, or GitHub App installation token, use `gh-auth-profile` to select the profile first.
   - `gh auth status`
   - `gh repo view --json nameWithOwner,url`
   - When a profile is selected, run every `gh` command in this workflow with that profile's one-command token environment.
   - If access fails, report the failing command, the missing GitHub capability, and the next permission step for the user, such as `gh auth login`, `gh auth refresh -s repo`, `gh auth refresh -s workflow`, org SSO authorization, or repository Actions read access.
3. Prefer PR checks when the branch has an associated PR:
   - `gh pr view --json number,url,headRefName,headRefOid,statusCheckRollup`
   - `gh pr checks`
4. Find relevant workflow runs:
   - `gh run list --branch <branch> --limit 10 --json databaseId,status,conclusion,workflowName,displayTitle,headSha,url`
   - prefer failed or cancelled runs matching the PR head SHA or current branch head.
5. Inspect failed jobs and logs:
   - `gh run view <run-id> --json jobs`
   - `gh run view <run-id> --log-failed`
   - identify the failed command, assertion, file path, dependency, or environment assumption from the logs.
6. Reproduce locally when practical:
   - run the smallest matching lint, test, build, or script command.
   - inspect project manifests and CI workflow files only as needed to map the job command to local commands.
7. Fix the root cause:
   - make the narrowest code, test, dependency, or workflow change that addresses the logged failure.
   - avoid unrelated cleanup.
8. Verify and report:
   - rerun the local failing command or nearest meaningful check.
   - report the failed workflow/run, root cause, files changed, and verification result.

## Guardrails

- Do not infer the cause from workflow or check names alone; inspect failed logs.
- Do not rerun workflow runs unless the user asks.
- Do not push commits or update PRs unless the user asks.
- Do not install dependencies, access private systems, or use paid services without explicit user intent.
- If `gh` is unauthenticated, missing, or blocked by sandbox/network restrictions, report the blocker and the command that failed.
- Do not use `gh auth switch` to change the active account. Use `gh-auth-profile` when repository-specific credentials are needed.
- If a GitHub command fails due to auth, OAuth scope, SAML SSO, org policy, missing repo role, Actions access, Checks access, or log visibility, stop and tell the user exactly what permission or approval is needed. Do not refresh scopes, change credentials, rerun workflows, or request elevated GitHub access unless the user explicitly asks.
- If logs point to secrets, tokens, or private URLs, avoid pasting sensitive values in the response.

## Common Commands

```bash
gh auth status
gh repo view --json nameWithOwner,url
gh pr view --json number,url,headRefName,headRefOid,statusCheckRollup
gh pr checks
gh run list --branch <branch> --limit 10 --json databaseId,status,conclusion,workflowName,displayTitle,headSha,url
gh run view <run-id> --json jobs
gh run view <run-id> --log-failed
```
