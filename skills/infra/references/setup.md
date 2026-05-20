# Setup And Validation

Read this file only when the local environment is missing the pieces needed to validate the skill or the bundled `modules/ensure_vm` + `stacks/` layout.

## Skill Validator

The skill validator script depends on `PyYAML`. Use a repo-local virtualenv instead of installing it globally:

```bash
cd "${CODEX_HOME:-$HOME/.codex}"
python3 -m venv .venv
.venv/bin/python -m pip install PyYAML
.venv/bin/python skills/.system/skill-creator/scripts/quick_validate.py skills/infra
```

Expected success output:

```text
Skill is valid!
```

## OpenTofu Or Terraform

Prefer an existing `tofu`, `opentofu`, or `terraform` binary if one is already installed. The module requires Terraform-compatible CLI behavior from version `1.4.0` or newer because it uses the built-in `terraform_data` resource. When none is available, a repo-local OpenTofu binary is acceptable.

This repo was validated on April 23, 2026 with OpenTofu `v1.11.6` on Linux `x86_64`.

For Linux `x86_64`, the repo-local install flow is:

```bash
cd "${CODEX_HOME:-$HOME/.codex}/skills/infra"
mkdir -p .tools/opentofu/1.11.6
curl -fL https://github.com/opentofu/opentofu/releases/download/v1.11.6/tofu_1.11.6_linux_amd64.zip -o .tools/opentofu/1.11.6/tofu_1.11.6_linux_amd64.zip
curl -fL https://github.com/opentofu/opentofu/releases/download/v1.11.6/tofu_1.11.6_SHA256SUMS -o .tools/opentofu/1.11.6/tofu_1.11.6_SHA256SUMS
grep 'tofu_1.11.6_linux_amd64.zip' .tools/opentofu/1.11.6/tofu_1.11.6_SHA256SUMS
sha256sum .tools/opentofu/1.11.6/tofu_1.11.6_linux_amd64.zip
unzip -o .tools/opentofu/1.11.6/tofu_1.11.6_linux_amd64.zip -d .tools/opentofu/1.11.6
.tools/opentofu/1.11.6/tofu version
```

For other platforms, use the official install guidance and release assets:

- `https://opentofu.org/docs/intro/install/standalone/`
- `https://github.com/opentofu/opentofu/releases`

## Module And Stack Validation

Validate the reusable module through a stack root (template or real fleet stack):

```bash
cd "${CODEX_HOME:-$HOME/.codex}/skills/infra"
cd stacks/_template
../../.tools/opentofu/1.11.6/tofu fmt
../../.tools/opentofu/1.11.6/tofu init -backend=false
../../.tools/opentofu/1.11.6/tofu validate
```

Expected success output from the final command:

```text
Success! The configuration is valid.
```

## Golden Template Baseline

For least-privilege provisioning, prepare a Proxmox cloud-init template that already contains stable guest policy. The runtime stack can then inject only dynamic values, such as SSH public keys, through Proxmox native cloud-init fields instead of requiring snippet upload permission.

Run these commands inside the VM before converting it to a Proxmox template.

Create the fixed cloud-init policy:

```bash
sudo tee /etc/cloud/cloud.cfg.d/99-infra-skill.cfg >/dev/null <<'EOF'
# Fixed policy for VMs provisioned by this infra skill.
manage_etc_hosts: false
disable_root: false
ssh_pwauth: false
chpasswd:
  expire: false
package_update: true
package_upgrade: true
ssh_deletekeys: true
EOF
```

If the fleet uses root SSH access, configure SSHD for key-only root login:

```bash
sudo install -d -m 0755 /etc/ssh/sshd_config.d
sudo tee /etc/ssh/sshd_config.d/99-infra-skill.conf >/dev/null <<'EOF'
PermitRootLogin prohibit-password
PasswordAuthentication no
PubkeyAuthentication yes
EOF
```

Install and enable the guest agent. The module uses the guest agent to discover VM IP addresses after provisioning:

```bash
sudo apt-get update
sudo apt-get install -y qemu-guest-agent cloud-init
sudo systemctl enable qemu-guest-agent
```

Before converting the VM to a template, clean per-instance state so cloned VMs regenerate their own identity:

```bash
sudo cloud-init clean --logs
sudo rm -f /etc/ssh/ssh_host_*
sudo truncate -s 0 /etc/machine-id
sudo rm -f /var/lib/dbus/machine-id
sudo shutdown -h now
```

Do not bake dynamic fleet values into the template:

- `hostname`
- `fqdn`
- `ssh_authorized_keys`
- fleet-specific IP addresses
- stack-specific API tokens or secrets

Those values should come from the stack, Proxmox native cloud-init settings, or generated artifacts.

## Snippet Upload Prerequisite

The default `cloud_init_delivery = "native"` mode does not need snippet files or storage upload permission. Use snippet delivery only when custom first-boot user-data cannot be baked into the template.

When `cloud_init_delivery = "snippet"`, this module renders snippet files locally under each stack's `.artifacts/snippets/` and references them using `cicustom`. Upload those files to your Proxmox snippets-enabled storage before running `tofu apply`.

The default filename pattern is:

- `<vm_name_prefix>-master-<n>_user_data.yml`
- `<vm_name_prefix>-worker-<n>_user_data.yml`
- `<vm_name_prefix>-control-<n>_user_data.yml` when using dedicated control VMs

For a single master with `vm_name_prefix=<vm_name_prefix>`, upload:

- `stacks/<fleet-name>/.artifacts/snippets/<vm_name_prefix>-master-1_user_data.yml`

to the storage configured by `pm_snippets_storage` under the `snippets/` content path.

For a reusable execution flow to create and verify a fleet, see
`references/provisioning-runbook.md`.

## Repo Hygiene

- `.venv/` and `.tools/` are intentionally git-ignored local helper paths.
- `stacks/<fleet-name>/.terraform.lock.hcl` should remain tracked for long-lived stacks when reproducibility matters.
- Do not commit `terraform.tfvars`, rendered SSH keys, rendered snippets, or generated inventory output.
