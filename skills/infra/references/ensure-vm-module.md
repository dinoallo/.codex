# Ensure VM Module

Read this file when you need the concrete behavior of the reusable `modules/ensure_vm` module and how it is consumed by stack roots.

## Overview

`modules/ensure_vm` is a reusable OpenTofu or Terraform module for cloning a Proxmox template into a master/worker fleet. It:

- generates one local SSH key pair,
- injects SSH keys through native Proxmox cloud-init fields by default,
- optionally renders one cloud-init user-data snippet per VM locally,
- optionally references pre-existing snippet files via `cicustom`,
- creates the VMs as linked clones,
- and writes an Ansible inventory from discovered guest IPs.
- isolates generated artifacts under a caller-provided `artifacts_dir`.

## File Map

- `modules/ensure_vm/providers.tf`: provider version constraints
- `modules/ensure_vm/variables.tf`: module inputs including `artifacts_dir`
- `modules/ensure_vm/locals.tf`: hostnames and artifact paths
- `modules/ensure_vm/ssh_key.tf`: generated ED25519 key pair
- `modules/ensure_vm/snippets.tf`: local snippet rendering
- `modules/ensure_vm/cloud_init.tpl`: user-data template with `manage_etc_hosts: false`
- `modules/ensure_vm/vm.tf`: VM clone resources and inventory generation
- `modules/ensure_vm/inventory.tpl`: Ansible inventory template
- `modules/ensure_vm/outputs.tf`: VM names and VMIDs
- `stacks/_template/`: starter stack for new fleets
- `ensure_vm/`: legacy-compatible stack wrapper around the module (with `moved` blocks)

## Auth Model

The module expects a Proxmox provider configuration from the caller stack:

- `telmate/proxmox` driven by `pm_api_url`, `pm_user`, `pm_api_token_id`, and `pm_api_token_secret`

## Important Inputs

- `pm_api_url`: Proxmox API endpoint
- `pm_user`: Proxmox user or service account
- `pm_api_token_id` / `pm_api_token_secret`: primary token inputs
- `pm_tls_insecure`: TLS verification toggle
- `pm_node`: target Proxmox node for VM creation
- `pm_storage`: storage used for VM disks and cloud-init disk
- `cloud_init_delivery`: `native` for least-privilege Proxmox cloud-init fields, or `snippet` for `cicustom` user-data
- `cloud_init_user`: guest user configured through Proxmox cloud-init
- `pm_snippets_storage`: snippets-enabled Proxmox storage referenced by `cicustom` when `cloud_init_delivery = "snippet"`
- `vm_template`: clonable Proxmox template identifier accepted by the active provider version
- `vm_name_prefix`: prefix used to derive hostnames
- `vm_master_count` / `vm_worker_count`: stable master/worker fleet sizing
- `vm_memory_mb`, `vm_cores`, `vm_disk_gb`: hardware sizing
- `artifacts_dir`: per-stack output directory for generated key, inventory, and optional snippets

## Generated Artifacts

By default, the module writes generated outputs under `<stack>/.artifacts/`:

- `.artifacts/id_ed25519_tofu`
- `.artifacts/ansible_inventory.ini`
- `.artifacts/snippets/<hostname>_user_data.yml` when `cloud_init_delivery = "snippet"`

The native cloud-init mode enables:

- SSH login for `cloud_init_user` with the generated public key
- no per-run snippet upload requirement

The optional snippet template enables:

- root SSH login with the generated public key
- host key regeneration via `ssh_deletekeys: true`
- `manage_etc_hosts: false`
- package update and upgrade on first boot

The inventory template groups hosts as:

- `first_master`
- `other_masters`
- `workers`

## Execution Flow

1. Generate the SSH key pair.
2. Compute master and worker hostnames.
3. When using native delivery, clone VMs from `vm_template` with Proxmox `ciuser` and `sshkeys`.
4. When using snippet delivery, render one snippet file per hostname under `<artifacts_dir>/snippets` and ensure matching snippet files exist in Proxmox snippet storage.
5. Discover guest IPs and render the Ansible inventory.

## Notes

- The VM config assumes `vmbr0`, DHCP, `cloud_init_user`, and the QEMU guest agent.
- The module adds an extra `scsi1` disk only when `vm_disk_gb > 0`.
- Treat `vm_template` as an identifier that must match the provider version and environment you are targeting.
- Use `cloud_init_delivery = "native"` unless the VM requires custom first-boot user-data that cannot be baked into the template.
- This module intentionally does not upload snippets to Proxmox; snippet upload is handled out of band when `cloud_init_delivery = "snippet"`.
- See `references/provisioning-runbook.md` for a concrete, reusable apply and verification sequence.
