# Workflow Patterns

## Contents

- CI workflow
- Matrix test workflow
- Release or publish workflow
- Deploy workflow
- Scheduled or manual workflow
- Reusable workflow
- Reusable workflow caller

## CI workflow

Use for build and test checks on pull requests and protected branches.

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - run: <install command>
      - run: <test command>
```

## Matrix test workflow

Use when policy requires multiple runtimes, operating systems, or architectures.

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, macos-latest]
    node: [20, 22]
runs-on: ${{ matrix.os }}
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-node@v4
    with:
      node-version: ${{ matrix.node }}
      cache: npm
```

Keep the matrix narrow. Split unrelated concerns into separate jobs instead of one large cartesian product.

## Release or publish workflow

Use for tags, releases, package publication, or artifact uploads.

```yaml
on:
  push:
    tags: ['v*']
permissions:
  contents: read
  packages: write
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: <build command>
      - run: <publish command>
        env:
          TOKEN: ${{ secrets.PUBLISH_TOKEN }}
```

Add `id-token: write` only when using OIDC. Keep publish credentials out of pull request workflows.

## Deploy workflow

Use when deployment should depend on prior validation and may require GitHub environments.

```yaml
permissions:
  contents: read
  deployments: write
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: <test command>
  deploy:
    needs: test
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: <deploy command>
```

Prefer environment protection rules over shell-based approval logic when the repo already uses environments.

## Scheduled or manual workflow

Use for cleanup, report generation, dependency refresh, or maintenance jobs.

```yaml
on:
  workflow_dispatch:
    inputs:
      target:
        required: false
        type: string
  schedule:
    - cron: '15 3 * * *'
```

Schedule runs use the default branch workflow definition. Document timezone assumptions when they matter.

## Reusable workflow

Use when several workflows share the same CI or deployment sequence.

```yaml
on:
  workflow_call:
    inputs:
      node-version:
        required: true
        type: string
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
```

Define clear inputs, secrets, and outputs. Keep reusable workflows generic and stable.

## Reusable workflow caller

Use a caller when the repo already publishes shared workflows.

```yaml
jobs:
  ci:
    uses: ./.github/workflows/reusable-ci.yml
    with:
      node-version: '22'
    secrets: inherit
```

Use `secrets: inherit` only when the callee genuinely needs the caller's secret set.
