# Provisioning Runbook

This runbook documents the standard workflow to create and verify a VM fleet with `modules/ensure_vm` via an isolated stack under `stacks/<fleet-name>/`.

## Scope

- Provision target: control, master, and worker VMs
- Prefix: configurable (`vm_name_prefix`)
- Module: `modules/ensure_vm`
- Stack root: `stacks/<fleet-name>/`
- IaC CLI: `../../.tools/opentofu/1.11.6/tofu` (from inside a stack)

## Prerequisites

1. `stacks/<fleet-name>/tf.vars` contains valid Proxmox API token credentials.
2. `pm_node`, `pm_storage`, and `vm_template` are valid for your environment.
3. For least-privilege provisioning, the VM template includes the baseline cloud-init and SSH policy from `references/setup.md`.
   The template's cloud-init default user should match `cloud_init_user` unless `set_proxmox_ciuser = true`.
4. If `cloud_init_delivery = "snippet"`, `pm_snippets_storage` is valid and matching snippet filenames exist in that storage before apply.

## Baseline Variables

Set these in `stacks/<fleet-name>/tf.vars`:

```hcl
vm_name_prefix      = "<vm_name_prefix>"
vm_master_count     = <master_count>
vm_worker_count     = <worker_count>
vm_control_count    = 0
cloud_init_delivery = "native"
cloud_init_user     = "root"
set_proxmox_ciuser  = false
artifacts_dir       = ".artifacts"
```

`artifacts_dir` should normally stay `.artifacts` so outputs remain stack-local.
When `vm_control_count = 0`, the first master acts as the control node. Set `vm_control_count > 0` only when you need dedicated control VMs. A worker-only topology is invalid.

Use `cloud_init_delivery = "snippet"` only when custom first-boot user-data cannot be baked into the template. In that mode, also set `pm_snippets_storage`.

## Provisioning Steps

1. Create a new stack from template and set values:

```bash
cp -R stacks/_template stacks/<fleet-name>
cp stacks/<fleet-name>/tf.vars.example stacks/<fleet-name>/tf.vars
```

2. Render and validate module inputs.

```bash
cd stacks/<fleet-name>
../../.tools/opentofu/1.11.6/tofu fmt
../../.tools/opentofu/1.11.6/tofu validate
```

3. If using native delivery, confirm the plan uses `sshkeys` without a `cicustom` value. It should not set `ciuser` unless `set_proxmox_ciuser = true`.

4. If using snippet delivery, confirm local rendered snippets exist for all hosts.

Examples:

- `.artifacts/snippets/<vm_name_prefix>-master-1_user_data.yml`
- `.artifacts/snippets/<vm_name_prefix>-worker-1_user_data.yml`
- `.artifacts/snippets/<vm_name_prefix>-control-1_user_data.yml` when using dedicated control VMs

5. If using snippet delivery, ensure matching filenames already exist in Proxmox snippet storage.

Examples:

- `<pm_snippets_storage>:snippets/<vm_name_prefix>-master-1_user_data.yml`
- `<pm_snippets_storage>:snippets/<vm_name_prefix>-worker-1_user_data.yml`
- `<pm_snippets_storage>:snippets/<vm_name_prefix>-control-1_user_data.yml` when using dedicated control VMs

6. Apply:

```bash
../../.tools/opentofu/1.11.6/tofu apply -auto-approve -var-file=tf.vars
```

7. If re-provisioning is required, force replacement:

```bash
../../.tools/opentofu/1.11.6/tofu apply -auto-approve -var-file=tf.vars -replace='module.ensure_vm.proxmox_vm_qemu.vm[0]'
```

## Verification Steps

1. Check output VM identity:

```bash
../../.tools/opentofu/1.11.6/tofu output vm_names
../../.tools/opentofu/1.11.6/tofu output control_vm_names
../../.tools/opentofu/1.11.6/tofu output control_vm_ipv4_addresses
../../.tools/opentofu/1.11.6/tofu output vm_vmid
```

2. Check discovered IPs from generated inventory:

```bash
sed -n '1,200p' .artifacts/ansible_inventory.ini
```

3. Verify the fixed cloud-init policy inside a guest:

```bash
ssh -i .artifacts/id_ed25519_tofu \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  <cloud_init_user>@<vm_ip> 'sudo cloud-init status --long && sudo grep -R "^manage_etc_hosts: false" /etc/cloud/cloud.cfg /etc/cloud/cloud.cfg.d/'
```

4. If using snippet delivery, verify cloud-init payload inside a guest via Proxmox guest-agent API:

```bash
curl -skS -H "Authorization: PVEAPIToken=<token_id>=<token_secret>" \
  "<pm_api_url>/nodes/<node>/qemu/<vmid>/agent/file-read?file=/var/lib/cloud/instance/cloud-config.txt"
```

Expected setting:

- `manage_etc_hosts: false`

5. Verify SSH:

```bash
ssh -i .artifacts/id_ed25519_tofu \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  <cloud_init_user>@<vm_ip> 'hostname'
```

6. Verify control-node SSH fan-out:

```bash
ssh -i .artifacts/id_ed25519_tofu \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  <cloud_init_user>@<control_ip> 'ssh -o BatchMode=yes <cloud_init_user>@<target_vm_ip> hostname'
```

## Known Failure Mode: SSH Key Mismatch

Symptom:

- `Permission denied (publickey,password)` after successful VM creation.

Likely causes:

- Proxmox snippet storage contains a stale `ssh_authorized_keys` value that does not match local `.artifacts/id_ed25519_tofu.pub`.
- The VM template does not permit key-only login for `cloud_init_user`.
- The stack changed `cloud_init_delivery` without replacing or re-running cloud-init on existing VMs.
- The control key delivery provisioner could not SSH to the resolved control node.

Recovery flow:

1. Read the target user's `authorized_keys` via guest-agent `file-read`.
2. Append the current key from `.artifacts/snippets/<hostname>_user_data.yml` when using snippet delivery, or from the generated public key in state/plan when using native delivery.
3. Write back with guest-agent `file-write`.
4. Re-test SSH.

## API Limitation Observed

In this environment, tested Proxmox storage upload endpoints did not accept `snippets` as a `content` type. When `cloud_init_delivery = "snippet"`, deliver snippet files out of band to snippet storage before apply.
