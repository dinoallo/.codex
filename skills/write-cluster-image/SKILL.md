---
name: write-cluster-image
description: Create or revise Sealos cluster image deploy files using patterns from the Sealos repository. Use when Codex needs to write or review deploy/Kubefile, images/shim/images, Helm charts, values files, App resources, ingress/config templates, or entrypoint scripts for Sealos cluster images, especially scratch-based images that install services with helm upgrade -i.
---

# Write Cluster Image

## Overview

Create Sealos cluster image deploy directories that package charts, image metadata, and install entrypoints using the nearest matching deploy pattern in the Sealos repository.

## Workflow

1. Inspect the target service, app runtime image, Kubernetes resources, and any nearby `deploy/` directory before creating new files.
2. Read [references/sealos-cluster-image.md](references/sealos-cluster-image.md) before implementing or reviewing deploy files.
3. Create or update only the deploy surface required by the task:
   - `Kubefile`
   - entrypoint script
   - `charts/<chart>/Chart.yaml`
   - `charts/<chart>/values.yaml`
   - optional `charts/<chart>/<service>-values.yaml`
   - `charts/<chart>/templates/*.yaml`
   - optional `images/shim/images`
4. Keep cluster-specific values out of static manifests when the value is available from `sealos-system/sealos-config`; inject it in the entrypoint with Helm `--set-string`.
5. Keep user-tunable defaults in the service values file copied to `/root/.sealos/cloud/values/core/<service>-values.yaml`; keep chart defaults complete enough for `helm template`.
6. Ensure chart defaults are renderable during `sealos build`; avoid `required` values that block image scanning unless the build pipeline supplies those values.
7. Verify with the smallest local checks available, usually `bash -n` for entrypoints and `helm lint` or `helm template` for charts.

## Review Workflow

When reviewing an existing cluster image deploy directory, use a fixed protocol:

1. Read [references/sealos-cluster-image.md](references/sealos-cluster-image.md).
2. Locate the target `deploy/` directory and identify its `Kubefile`, entrypoint, chart directory, values files, templates, and optional `images/shim/images`.
3. Run the bundled static verifier from this skill directory:

   ```bash
   python3 scripts/verify-cluster-image.py <deploy-dir> --ensure-helm
   ```

   Use `--chart <chart>`, `--release <release>`, and `--namespace <namespace>` when those are known. Keep `--ensure-helm` enabled for chart reviews unless the user disallows network access; the verifier uses system `helm` when present and otherwise downloads a sha256-verified Helm binary into a temporary tool cache.
4. If Helm download fails because of sandboxed or restricted network access, rerun the same verifier command with the environment's normal approval/escalation mechanism. If approval is not granted, report Helm checks as `UNKNOWN` and continue with static checks.
5. Manually inspect any `WARN`, `FAIL`, and `UNKNOWN` items against the reference. The script is a gate, not a substitute for judgment.
6. Report results using this shape:

   ```text
   Cluster Image Review

   Result: PASS | PASS_WITH_NOTES | FAIL

   Findings:
   1. FAIL <file>: <reason>
   2. WARN <file>: <reason>

   Verification:
   - python3 scripts/verify-cluster-image.py <deploy-dir> --ensure-helm: <result>
   - Any extra checks run: <result>

   Unknowns:
   - <tool or cluster-specific check that could not be verified>
   ```

Do not run cluster-mutating commands such as the entrypoint itself, `helm upgrade`, or `sealos run` during review unless the user explicitly asks for live-cluster verification.

## Design Rules

- Prefer the nearest existing Sealos deploy pattern over inventing a new layout.
- Use `FROM scratch` cluster images that copy deploy artifacts; the application runtime image belongs in Helm values, not in the cluster image `FROM`.
- Treat `Kubefile` `ENV` entries as project-specific install defaults. Do not copy another service's `ENV` block unless each variable is consumed by this service's entrypoint or chart.
- Use stable service names consistently across `RELEASE_NAME`, `RELEASE_NAMESPACE`, `SERVICE_NAME`, `fullnameOverride`, labels, adoption logic, and values file paths.
- Use `--set-string` for auto-configured strings, domains, ports, booleans represented as strings, URLs, and tokens. Escape commas before adding values to Helm arguments.
- Add resource adoption only for resources that may already exist from a previous non-Helm or older Helm install.
- Put Sealos `App` resources inside the Helm chart for cluster images; standalone `.tmpl` manifests are useful for review but are not installed by a Helm-only entrypoint.
- Do not commit real secrets, cluster domains, tokens, or production URLs as required defaults. Use safe local defaults such as `127.0.0.1.nip.io`, empty strings, or internal service DNS names.

## Verification

Run checks that match the files changed:

- Entrypoints: `bash -n deploy/<entrypoint>.sh`
- Charts: `helm lint deploy/charts/<chart>` and `helm template <release> deploy/charts/<chart> -n <namespace>`
- Full local review gate: `python3 scripts/verify-cluster-image.py <deploy-dir> --ensure-helm`
- Cluster image build, when requested and tools are present: `sealos build -t <image> deploy`

If `helm` is unavailable, use the bundled verifier with `--ensure-helm` to download and use a local Helm binary. If download is unavailable, state that clearly and still run the remaining static checks.
