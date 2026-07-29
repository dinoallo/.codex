---
name: gh-edit-issue
description: Edit existing GitHub issues with gh CLI. Use when Codex is asked to update issue titles or bodies, add or remove labels, assignees, milestones, projects, types, parents, blocking links, or sub-issues, add comments, close or reopen issues, or resolve repository auth profiles before issue edits. This skill is specifically for `gh issue edit`, `gh issue comment`, `gh issue close`, and `gh issue reopen` workflows, not creating issues or pull requests.
---

# GH Edit Issue

## Overview

Use `gh` CLI to update an existing issue without changing unrelated local work. Prefer explicit, non-interactive commands and verify the issue state before and after each modification.

## Workflow

1. Identify the target issue:
   - Prefer a user-provided issue number, URL, or explicit selector.
   - If the user references an issue indirectly, resolve that reference before editing.
   - Inspect local context with `git status --short --branch`, `git branch --show-current`, and `git remote -v` when the repository is not explicit.
2. Resolve the target repository and auth profile before any `gh` command:
   - Infer the target repository from an issue URL, explicit `--repo` or URL arguments, configured remote URLs from `git remote -v`, or the current repository context.
   - Normalize the target to `host/owner/repo`, such as `github.com/labring/sealos`.
   - Do not use `gh auth status`, `gh repo view`, `gh issue`, or `gh api` to resolve the target before this auth gate.
   - If `gh-auth-profile` is available, read it and attempt to match a profile for the normalized target before any bare `gh` command.
   - Treat non-default auth as required for organization-owned repositories, fine-grained PAT workflows, GHES hosts, GitHub App installation tokens, project edits, or when the target owner differs from the current fork or push remote owner. If required auth has no matching profile, stop and show the `gh-auth-profile` first-use or no-match prompt instead of falling back to bare `gh`.
   - If a profile matches, select it and run every `gh` command in this workflow with that profile's one-command token environment.
   - Only after confirming that no profile rule matches and non-default auth is not required may bare `gh` commands be used.
3. Confirm GitHub CLI access and repository context with the resolved auth mode:
   - With a matched profile: `<profile-env> gh auth status`
   - With a matched profile: `<profile-env> gh repo view <owner/repo> --json nameWithOwner,url,defaultBranchRef`
   - Without a matched profile, only when allowed by step 2: `gh auth status`
   - Without a matched profile, only when allowed by step 2: `gh repo view <owner/repo> --json nameWithOwner,url,defaultBranchRef`
   - Treat missing `gh`, missing auth, permission failures, and sandbox/network failures as blockers.
   - If access fails, report the failing command, the missing GitHub capability, and the next permission step for the user, such as `gh auth login`, `gh auth refresh -s repo`, `gh auth refresh -s read:org`, org SSO authorization, or repo write access.
4. Snapshot the issue before editing:
   - Run with the resolved auth mode: `gh issue view <selector> --json number,url,title,state,body,issueType,labels,assignees,milestone,projectItems,parent,blocking,blockedBy,subIssues`
   - Use this to confirm the target, avoid editing the wrong issue, and compare the result.
5. Choose the smallest command for the requested change:
   - Use `gh issue edit` for title, body, labels, assignees, milestone, project, issue type, parent, blocking, blocked-by, and sub-issue changes.
   - Use `gh issue comment` to add or update comments.
   - Use `gh issue close` or `gh issue reopen` only when the user explicitly asks for that state change.
   - Keep comment edits separate from issue body edits unless the user asked for both.
6. Prepare multiline text safely:
   - Use `--body-file <file>` for issue body edits and `gh issue comment --body-file <file>` for multiline comments.
   - A temporary file under `/tmp` is acceptable.
   - Preserve meaningful issue template sections unless the user asks to replace the body wholesale.
7. Review the title, body, and comment text before editing:
   - Inspect the final text before running `gh issue edit`, `gh issue comment`, `gh issue close`, or `gh issue reopen`.
   - Do not paste secrets, tokens, private URLs, internal incident text, customer identifiers, or machine-specific paths unless the user explicitly asks and the content is safe for the target repository.
   - Redact or remove likely secrets and credentials, including private keys, certificates, tokens, OAuth/JWT/Bearer values, passwords, API keys, cloud keys, database DSNs, kubeconfigs, `.env` content, `ghp_`, `github_pat_`, and fine-grained PAT values.
   - If the body or comment may expose private information, stop and ask for a sanitized version instead of editing the issue.
8. Run the edit non-interactively:
   - Run every `gh issue edit`, `gh issue comment`, `gh issue close`, and `gh issue reopen` command with the resolved auth mode.
   - Pass explicit flags for every requested change.
   - Avoid `--web`, `--editor`, and interactive prompts unless the user asks for the browser or editor flow.
   - Combine compatible `gh issue edit` flags in one command when that is clear and reviewable.
   - If project edits fail due to missing `project` scope, report `gh auth refresh -s project` as the required auth step.
9. Verify and report:
   - Run with the resolved auth mode: `gh issue view <selector> --json number,url,title,state,issueType,labels,assignees,milestone,projectItems,parent,blocking,blockedBy,subIssues`
   - Report the issue URL, the fields changed, and the verification command.

## Guardrails

- Use `gh` CLI for GitHub issue edits; do not switch to browser or raw API workflows unless the user asks.
- Before running any bare `gh auth status`, `gh repo view`, `gh issue`, or `gh api`, first resolve whether a `gh-auth-profile` rule matches the target repository. If a matching profile exists, never run bare `gh`; run every command with the profile's one-command token environment.
- For organization-owned repositories, fine-grained PAT workflows, GHES hosts, GitHub App installation tokens, project edits, or when the target owner differs from the current fork or push remote owner, treat non-default auth as required and use `gh-auth-profile` first.
- Do not create a new issue or pull request from this skill. Use `gh-create-issue` for new issues and `gh-create-pr` or `gh-edit-pr` for PR workflows.
- Do not commit, amend, rebase, merge, push, or rewrite Git history unless the user explicitly asks for that Git operation.
- Do not change the issue state, labels, assignees, milestone, project, or type unless the user asked or the repository convention is already clear.
- Do not use `gh auth switch` to change the active account. Use `gh-auth-profile` when repository-specific credentials are needed.
- If any GitHub operation fails due to auth, OAuth scope, SAML SSO, org policy, missing repo role, branch protection, or project permissions, stop and tell the user exactly what permission or approval is needed. Do not attempt to change credentials, refresh scopes, or bypass policy unless the user explicitly asks.
- Avoid pasting secrets or sensitive internal URLs from issue bodies, comments, logs, or command output.

## Command Patterns

Use these patterns only after the target/profile gate has selected the resolved auth mode. If a profile was selected, replace bare `gh` with that profile's one-command token environment plus `gh`.

Edit title and body:

```bash
gh issue edit <selector> --title "<title>" --body-file <body-file>
```

Change labels, assignees, and metadata:

```bash
gh issue edit <selector> --add-label "bug,help wanted" --remove-label "needs-triage"
gh issue edit <selector> --add-assignee "@me" --remove-assignee old-user
gh issue edit <selector> --add-project "Roadmap" --remove-project "v1"
gh issue edit <selector> --milestone "Version 1"
gh issue edit <selector> --type Bug
gh issue edit <selector> --parent 100
gh issue edit <selector> --add-blocking 300 --add-blocked-by 200
```

Add or update a comment:

```bash
gh issue comment <selector> --body-file <comment-file>
gh issue comment <selector> --edit-last --body-file <comment-file>
```

Close or reopen only when explicitly requested:

```bash
gh issue close <selector> --comment "<comment>"
gh issue close <selector> --reason "not planned"
gh issue reopen <selector> --comment "<comment>"
```

Verify before and after:

```bash
gh issue view <selector> --json number,url,title,state,issueType,labels,assignees,milestone,projectItems,parent,blocking,blockedBy,subIssues
```
