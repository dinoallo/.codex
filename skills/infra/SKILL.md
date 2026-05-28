---
name: infra
description: Use when the user wants to provision or modify a small Proxmox VM fleet with OpenTofu or Terraform, especially linked clones from a cloud-init template, control/master/worker node topology, least-privilege native cloud-init SSH key injection, optional cicustom snippet-based cloud-init, generated Ansible inventory, or a control-node SSH key pair. This skill bundles a reusable `modules/ensure_vm` module and stack wrappers for per-fleet state isolation.
---

# Infra

Use this skill when the task is to create, adjust, or explain the bundled Proxmox OpenTofu layout. The reusable module is in `modules/ensure_vm`, while each fleet should run from an independent root stack under `stacks/<fleet>`.

## Quick Start

1. Default happy path: initialize the reusable module and a new isolated stack in the user's current repository, then ask the user to fill `stacks/<fleet>/tf.vars` locally. Do not ask for API token secrets in chat.
2. If the user says "initialize", "create a test stack", or similar, copy the bundled `modules/ensure_vm` and `stacks/_template` layout into the current working directory, create `stacks/<fleet>/`, add git ignores for `tf.vars`, state, and `.artifacts/`, then stop before planning.
3. After the user says they filled `tf.vars`, verify the file exists without printing its contents, then run `tofu fmt`, `tofu init -backend=false`, `tofu validate`, and `tofu plan -var-file=tf.vars` from `stacks/<fleet>/`.
4. Run `apply` or `destroy` only after explicit user confirmation.
5. Keep secrets out of version control and out of chat. Prefer a git-ignored `tf.vars` for real credentials.
6. Read `references/setup.md` only when the local environment is missing validation dependencies, an IaC CLI, or template preparation details.
7. Read `references/ensure-vm-module.md` only when you need variable, provider, or file-level details.
8. Read `references/provisioning-runbook.md` when you need the standard end-to-end provisioning and verification flow for this module.

## Workflow

1. Start by deciding the fleet stack name, defaulting to a short test name such as `pve-test` when the user has no preference.
2. Initialize files first when the user wants a new stack: copy the packaged module/template, preserve isolated state under `stacks/<fleet>/`, and generate only examples/placeholders for Proxmox values.
3. Ask the user to create or edit `stacks/<fleet>/tf.vars` locally. It is acceptable to collect non-secret facts in chat, such as node, storage, template, topology, and Proxmox major version, but never require token secrets in chat.
4. Confirm the target Proxmox environment from `tf.vars` or user-provided non-secret facts: API endpoint, auth model, node, storage, and clonable template.
5. Prefer `cloud_init_delivery = "native"` for least-privilege provisioning. Confirm the template has the baseline cloud-init and SSH policy from `references/setup.md`.
6. Confirm snippet storage and upload path before apply when using `cicustom`: rendered local snippets must exist in Proxmox snippet storage under matching filenames.
7. Adjust counts and sizing first: control count, master count, worker count, memory, cores, and optional extra disk.
   If `vm_control_count = 0`, the first master acts as the control node. A worker-only fleet is invalid.
8. Review the network and cloud-init assumptions before changing the module:
   `vmbr0`, DHCP, `cloud_init_user`, optional `cicustom` snippet references, and guest-agent-based IP discovery.
9. If setup, validation tooling, or template preparation details are missing, read `references/setup.md`.
10. Validate with `tofu fmt` and `tofu validate` when the CLI is available.
11. Run `tofu plan` or `terraform plan` only when the user has provided a local `tf.vars` file or explicitly provided real credentials through another safe local mechanism.

## Operational Rules

- The module uses `telmate/proxmox` for VM creation.
- The module defaults to native Proxmox cloud-init fields for SSH key injection and does not require snippet upload permission.
- The preferred interaction model is init-only first, user-filled local `tf.vars` second, then plan/apply after confirmation.
- The module supports control, master, and worker roles. When no dedicated control VM is requested, the first master is the control node.
- The module must create at least one master or one dedicated control node; creating only workers is invalid.
- The generated key pair in `.artifacts/id_ed25519_tofu` and `.artifacts/id_ed25519_tofu.pub` is the control-node login key pair.
- Control nodes receive the same private/public key pair under `~/.ssh/id_ed25519_tofu*` and all node host public keys in `~/.ssh/known_hosts`, so the control node can SSH to all fleet nodes authorized with the generated public key.
- The module does not upload snippets to Proxmox; when `cloud_init_delivery = "snippet"`, it only renders them locally.
- Prefer baking stable cloud-init policy into the VM template and injecting only dynamic values such as SSH keys through Proxmox native cloud-init fields.
- Treat snippet upload permission as an elevated capability because `cicustom` user-data runs as first-boot root configuration.
- Treat rendered keys, rendered snippet YAML files, and generated inventory as ephemeral outputs, not committed source.
- Do not print `tf.vars` contents. When checking it, verify existence or summarize only non-secret fields.
- Treat `.venv/` and `.tools/` as repo-local helper paths. They are for validation convenience, not source artifacts.
- When modifying the packaged module, keep `modules/ensure_vm/` and `references/ensure-vm-module.md` aligned.
- `vm_template` is a provider-specific template identifier. Keep its format aligned with the provider version in use in the environment you are targeting.

## Reference Map

- `references/setup.md`: local bootstrap and validation commands for this repo, including the skill validator and repo-local OpenTofu usage.
- `references/ensure-vm-module.md`: file map, inputs, outputs, authentication behavior, and the execution flow of the bundled module.
- `references/provisioning-runbook.md`: general end-to-end procedure to provision and verify VMs, including SSH mismatch recovery.
