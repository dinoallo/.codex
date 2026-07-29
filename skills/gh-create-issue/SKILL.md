---
name: gh-create-issue
description: Create GitHub issues with gh CLI. Use when Codex is asked to open, file, create, or draft a GitHub issue from the current repository or a specified repo, including repository auth profile resolution, issue title/body drafting, template selection, label/assignee/milestone/project assignment, duplicate issue checks, and post-create confirmation. This skill is specifically for `gh issue create` workflows, not pull requests or Git history work.
---

# GH Create Issue

## Overview

Use `gh` CLI to file an issue in the target repository while preserving unrelated local work. Prefer explicit, non-interactive commands so the issue title, body, labels, assignee, milestone, project, and issue type are reviewable.

## Workflow

1. Inspect local repository context when the repo is not explicit:
   - `git status --short --branch`
   - `git branch --show-current`
   - `git remote -v`
   - Preserve unrelated dirty files. If there are uncommitted changes, note that they are not part of the issue unless the user explicitly asks for a patch or diff summary.
2. Resolve the target repository and auth profile before any `gh` command:
   - Infer the target repository from the user request, explicit `--repo` or URL arguments, and `git remote -v`.
   - Normalize the target to `host/owner/repo`, such as `github.com/labring/sealos`.
   - Do not use `gh auth status`, `gh repo view`, `gh issue`, or `gh api` to resolve the target before this auth gate.
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
4. Check for an existing issue before creating a duplicate:
   - Search open issues with the closest title or topic when the request is likely to duplicate existing work:
     - `gh issue list --state open --search 'in:title <keywords>' --json number,url,title`
   - If the user provides an issue number or URL as related context, use it only as a reference or linkage when that relationship is explicit.
   - If a clear match exists, report it instead of creating a duplicate unless the user explicitly asks for a separate issue.
   - Treat duplicate detection as best-effort; issue titles are fuzzy.
5. Prepare the issue title and body:
   - Derive a concise title from the request or observed problem.
   - Use an existing repository issue template if one exists and is relevant.
   - For bug reports, prefer the concrete shape:
     - Summary
     - Steps to Reproduce
     - Expected Behavior
     - Actual Behavior
     - Environment / Notes
   - For feature requests, prefer:
     - Summary
     - Problem / Motivation
     - Proposed Direction
     - Notes
   - Do not paste secrets, tokens, private URLs, internal incident text, customer identifiers, or machine-specific paths unless the user explicitly asks and the content is safe for the target repository.
   - Use `--body-file` for multiline bodies. A temporary file under `/tmp` is acceptable.
6. Review the title and body before creation:
   - Inspect the final title and body file before running `gh issue create`.
   - Redact or remove likely secrets and credentials, including private keys, certificates, tokens, OAuth/JWT/Bearer values, passwords, API keys, cloud keys, database DSNs, kubeconfigs, `.env` content, `ghp_`, `github_pat_`, and fine-grained PAT values.
   - If the body may expose private information, stop and ask for a sanitized body instead of creating the issue.
7. Create the issue non-interactively:
   - Run with the resolved auth mode: `gh issue create --title "<title>" --body-file <body-file>`
   - Add requested metadata with `--label`, `--assignee`, `--milestone`, `--project`, `--type`, `--parent`, `--blocking`, or `--blocked-by` when the user asks or repository convention is clear.
   - Use `--template <name>` only when the repository template is the right starting point.
   - Avoid `--web` unless the user specifically wants the browser flow.
   - If adding to a project fails due to missing `project` scope, report `gh auth refresh -s project` as the required auth step.
8. Confirm and report:
   - Run with the resolved auth mode: `gh issue view <number> --json number,url,title,state,issueType,labels,assignees,milestone,projectItems,parent,blocking,blockedBy`
   - Report the issue URL, title, state, and any metadata that was set.

## Default Issue Body Template

Use this fallback body when the repository has no issue template, or when the repository template is irrelevant. Replace the guidance with concrete content; do not leave placeholders, examples, or empty sections in the final body.

```markdown
## Summary

Explain the issue briefly.

## Problem

Describe the bug, gap, or request.

## Impact

Describe who is affected and how.

## Proposed Direction

Describe the expected fix, behavior, or next step.

## Notes

Use `None` only when there is genuinely nothing else to add.
```

- Keep tiny issues shorter when appropriate, but still state the problem and expected outcome.
- Omit `Notes` when there is no relevant context.
- Do not add a verification section to this template unless the user explicitly wants one or the repository template requires it.

## Guardrails

- Use `gh` CLI for GitHub issue creation; do not switch to browser or raw API workflows unless the user asks.
- Before running any bare `gh auth status`, `gh repo view`, `gh issue`, or `gh api`, first resolve whether a `gh-auth-profile` rule matches the target repository. If a matching profile exists, never run bare `gh`; run every command with the profile's one-command token environment.
- For organization-owned repositories, fine-grained PAT workflows, GHES hosts, GitHub App installation tokens, or when the target owner differs from the current fork or push remote owner, treat non-default auth as required and use `gh-auth-profile` first.
- Do not create or edit pull requests from this skill. Use `gh-create-pr` or `gh-edit-pr` for PR workflows.
- Do not commit, amend, rebase, merge, push, or rewrite Git history unless the user explicitly asks for that Git operation.
- Do not add labels, assignees, milestones, projects, or issue type unless the user asks or the repository convention is already clear.
- Do not use `gh auth switch` to change the active account. Use `gh-auth-profile` when repository-specific credentials are needed.
- If any GitHub operation fails due to auth, OAuth scope, SAML SSO, org policy, missing repo role, branch or project permission, stop and tell the user exactly what permission or approval is needed. Do not attempt to change credentials, refresh scopes, or bypass policy unless the user explicitly asks.
- Avoid pasting secrets or sensitive internal URLs from issue templates, logs, comments, or command output.

## Command Patterns

Use these patterns only after the target/profile gate has selected the resolved auth mode. If a profile was selected, replace bare `gh` with that profile's one-command token environment plus `gh`.

Create an issue:

```bash
gh issue create --title "<title>" --body-file <body-file>
```

Create an issue with metadata:

```bash
gh issue create --title "<title>" --body-file <body-file> --label bug --assignee "@me" --milestone "v1.0" --project "Roadmap" --type Bug
```

Confirm the created or existing issue:

```bash
gh issue view <number> --json number,url,title,state,issueType,labels,assignees,milestone,projectItems,parent,blocking,blockedBy
```
