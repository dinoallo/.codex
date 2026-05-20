---
name: proxmox-ensure-vm
description: Use when the user wants to provision or modify a small Proxmox VM fleet with OpenTofu or Terraform, especially linked clones from a cloud-init template, control/master/worker node topology, least-privilege native cloud-init SSH key injection, optional cicustom snippet-based cloud-init, generated Ansible inventory, or a control-node SSH key pair. This skill bundles a reusable `modules/ensure_vm` module and stack wrappers for per-fleet state isolation.
---

# Proxmox Ensure VM

Use this skill when the task is to create, adjust, or explain the bundled Proxmox OpenTofu layout. The reusable module is in `modules/ensure_vm`, while each fleet should run from an independent root stack under `stacks/<fleet>`.

## Quick Start

1. Decide whether the user wants to:
   - create or modify a fleet stack under `stacks/`,
   - use `modules/ensure_vm` in another repo,
   - or modify the skill's packaged module itself.
2. Keep secrets out of version control. Prefer environment variables or a git-ignored `terraform.tfvars`.
3. Run OpenTofu or Terraform from an isolated stack directory (`stacks/<fleet>/`) when planning or applying.
4. Read `references/setup.md` only when the local environment is missing validation dependencies or an IaC CLI.
5. Read `references/ensure-vm-module.md` only when you need variable, provider, or file-level details.
6. Read `references/provisioning-runbook.md` when you need the standard end-to-end provisioning and verification flow for this module.

## Workflow

1. Confirm the target Proxmox environment: API endpoint, auth model, node, storage, and clonable template.
2. Prefer `cloud_init_delivery = "native"` for least-privilege provisioning. Confirm the template has the baseline cloud-init and SSH policy from `references/setup.md`.
3. Confirm snippet storage and upload path before apply when using `cicustom`: rendered local snippets must exist in Proxmox snippet storage under matching filenames.
4. Adjust counts and sizing first: control count, master count, worker count, memory, cores, and optional extra disk.
   If `vm_control_count = 0`, the first master acts as the control node. A worker-only fleet is invalid.
5. Review the network and cloud-init assumptions before changing the module:
   `vmbr0`, DHCP, `cloud_init_user`, optional `cicustom` snippet references, and guest-agent-based IP discovery.
6. If setup, validation tooling, or template preparation details are missing, read `references/setup.md`.
7. Validate with `tofu fmt` and `tofu validate` when the CLI is available.
8. Run `tofu plan` or `terraform plan` only when the user has provided real credentials or a local tfvars file.

## Operational Rules

- The module uses `telmate/proxmox` for VM creation.
- The module defaults to native Proxmox cloud-init fields for SSH key injection and does not require snippet upload permission.
- The module supports control, master, and worker roles. When no dedicated control VM is requested, the first master is the control node.
- The module must create at least one master or one dedicated control node; creating only workers is invalid.
- The generated key pair in `.artifacts/id_ed25519_tofu` and `.artifacts/id_ed25519_tofu.pub` is the control-node login key pair.
- Control nodes receive the same private/public key pair under `~/.ssh/id_ed25519_tofu*` and all node host public keys in `~/.ssh/known_hosts`, so the control node can SSH to all fleet nodes authorized with the generated public key.
- The module does not upload snippets to Proxmox; when `cloud_init_delivery = "snippet"`, it only renders them locally.
- Prefer baking stable cloud-init policy into the VM template and injecting only dynamic values such as SSH keys through Proxmox native cloud-init fields.
- Treat snippet upload permission as an elevated capability because `cicustom` user-data runs as first-boot root configuration.
- Treat rendered keys, rendered snippet YAML files, and generated inventory as ephemeral outputs, not committed source.
- Treat `.venv/` and `.tools/` as repo-local helper paths. They are for validation convenience, not source artifacts.
- When modifying the packaged module, keep `modules/ensure_vm/` and `references/ensure-vm-module.md` aligned.
- `vm_template` is a provider-specific template identifier. Keep its format aligned with the provider version in use in the environment you are targeting.

## Reference Map

- `references/setup.md`: local bootstrap and validation commands for this repo, including the skill validator and repo-local OpenTofu usage.
- `references/ensure-vm-module.md`: file map, inputs, outputs, authentication behavior, and the execution flow of the bundled module.
- `references/provisioning-runbook.md`: general end-to-end procedure to provision and verify VMs, including SSH mismatch recovery.
