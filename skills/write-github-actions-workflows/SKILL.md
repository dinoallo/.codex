---
name: write-github-actions-workflows
description: Draft and revise GitHub Actions workflow files in `.github/workflows/*.yml`, including CI, release, deploy, scheduled, manual, and reusable workflows. Use when Codex needs to create a new workflow, modify triggers/jobs/permissions, convert shell automation into GitHub Actions, add matrix or caching, harden workflow security, or debug workflow structure and expressions.
---

# Write GitHub Actions Workflows

## Overview

Write or revise GitHub Actions workflow YAML with repository-aware defaults. Inspect existing workflows, project manifests, and build scripts first, then produce the smallest workflow that satisfies the requested automation.

## Authoring Flow

1. Read existing `.github/workflows/*.yml` files before introducing a new pattern.
2. Inspect nearby build and test entry points such as `package.json`, `Makefile`, `pyproject.toml`, `go.mod`, or repo scripts.
3. Classify the request:
   - CI validation
   - release or publish
   - deploy
   - scheduled maintenance
   - manual dispatch
   - reusable workflow
4. Choose the trigger set and job graph before writing YAML.
5. Add explicit `permissions`, `runs-on`, and `timeout-minutes`.
6. Validate with the smallest meaningful local check available in the repo.

## Workflow Decisions

- Prefer `pull_request` for pre-merge validation.
- Add `push` only when branch or tag runs matter after merge or for protected branches.
- Use `workflow_dispatch` for manual runs with optional inputs.
- Use `schedule` for periodic jobs and keep cron expressions quoted.
- Use `workflow_call` when the repo already centralizes repeated CI or deploy logic.
- Add `concurrency` when overlapping runs on the same ref should cancel.
- Add a matrix only when multiple versions, operating systems, or targets are required by policy.

## Authoring Rules

- Preserve existing naming, action versions, runner choices, and cache strategy unless the request calls for a change.
- Prefer maintained first-party or widely used actions over ad hoc shell when they clearly reduce risk.
- Default top-level `permissions` to the least privilege that works, usually `contents: read`.
- Escalate permissions only for the job that needs them when possible.
- Separate validation, build, publish, and deploy concerns into distinct jobs when they have different trust or permission requirements.
- Use `needs` and job outputs rather than repeating expensive setup across unrelated jobs.
- Gate writes, deployments, and comment-posting steps so they do not run on untrusted fork code by accident.
- Keep secrets, tokens, and environment assumptions explicit in the final explanation.

## Use References

- Read `references/workflow-patterns.md` for skeletons and selection guidance.
- Read `references/review-checklist.md` when the workflow includes secrets, caching, deploys, matrices, or PR-triggered writes.

## Delivery Expectations

- Place new workflows under `.github/workflows/<descriptive-name>.yml`.
- Explain behavior changes when editing an existing workflow.
- Call out required secrets, variables, environments, or branch assumptions.
- State what was validated locally and what still depends on GitHub runtime behavior.
