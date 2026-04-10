# Review Checklist

## Contents

- Before editing
- Triggers and conditions
- Permissions and secrets
- Concurrency and cancellation
- Job structure
- Caching and artifacts
- Common failure modes
- Validation

## Before editing

- Read every existing file in `.github/workflows/` that overlaps the request.
- Reuse existing action majors, runner labels, and naming conventions unless there is a reason to change them.
- Inspect the commands the workflow will run and verify they exist in repo scripts or docs.

## Triggers and conditions

- Confirm whether the workflow should run on `pull_request`, `push`, `workflow_dispatch`, `schedule`, `workflow_call`, or tag pushes.
- Avoid write operations on untrusted pull request code.
- Use `if:` sparingly and keep the predicate readable.
- Be careful with `github.ref` versus PR metadata; PR events do not behave like branch push events.

## Permissions and secrets

- Start with top-level `permissions: { contents: read }` unless the workflow truly needs more.
- Add `pull-requests: write`, `packages: write`, `deployments: write`, or `id-token: write` only when the workflow behavior requires them.
- Keep publish tokens, cloud credentials, and deployment secrets out of generic CI jobs.
- Do not echo secrets or derived credentials.
- Treat `pull_request_target` as privileged. Use it only with deliberate constraints and without running untrusted checked-out code.

## Concurrency and cancellation

- Add `concurrency` to long-running CI and deploy workflows when superseded runs should cancel.
- Group concurrency by workflow and ref unless the workflow needs a broader lock.
- Avoid cancellation for release or migration workflows that must run to completion.

## Job structure

- Add `timeout-minutes` to jobs that could hang.
- Split privileged jobs from unprivileged test jobs.
- Use `needs` for ordering instead of shelling multiple phases into one job.
- Keep `runs-on` explicit.

## Caching and artifacts

- Prefer built-in caching support in setup actions when available.
- Cache dependency directories, not full worktrees.
- Upload artifacts only when another job or humans need them.
- Be explicit about retention when artifacts are large or sensitive.

## Common failure modes

- Missing `actions/checkout` before reading repository files.
- Using secrets in fork PR contexts where they are unavailable.
- Broad matrices that multiply runtime and cost without clear value.
- Cron expressions left unquoted.
- Reusable workflow inputs or outputs that do not match the caller.
- Jobs that write comments, releases, or deployments without matching permissions.

## Validation

- Run the repo command the workflow will invoke whenever practical.
- If the repo has a YAML or workflow linter, use it.
- If no local validator exists, at least inspect for YAML shape, missing inputs, job references, and permission mismatches.
- Report anything that still needs a real GitHub run to prove behavior.
