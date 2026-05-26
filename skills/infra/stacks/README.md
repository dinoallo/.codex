# Stack Layout

Each subdirectory under `stacks/` is an independent root module with its own state and fleet configuration.

## Create A New Fleet Stack

The default workflow is init-only first, local secret entry second, then plan/apply after confirmation. A concise user prompt can be:

```text
$proxmox-ensure-vm Initialize stacks/pve-test in the current directory.
Do not plan or apply yet. I will fill stacks/pve-test/tf.vars locally.
```

1. Copy `_template` to a new folder and create a local variables file:

```bash
cp -R stacks/_template stacks/<fleet-name>
cp stacks/<fleet-name>/tf.vars.example stacks/<fleet-name>/tf.vars
```

2. Edit `stacks/<fleet-name>/tf.vars` with your prefix, counts, and Proxmox settings. Keep token secrets in this local file, not in chat or committed source.
   Keep at least one master or one dedicated control node. Worker-only fleets are invalid.
   Leave `vm_control_count = 0` to use the first master as the control node.
3. Keep `cloud_init_delivery = "native"` for least-privilege provisioning. In native mode, leave `set_proxmox_ciuser = false` and make sure the template's cloud-init default user matches `cloud_init_user`. Use `cloud_init_delivery = "snippet"` only when custom first-boot user-data cannot be baked into the template.
4. Run OpenTofu in that folder. Plan first; apply only after reviewing the plan:

```bash
cd stacks/<fleet-name>
../../.tools/opentofu/1.11.6/tofu init -backend=false
../../.tools/opentofu/1.11.6/tofu fmt
../../.tools/opentofu/1.11.6/tofu validate
../../.tools/opentofu/1.11.6/tofu plan -var-file=tf.vars
../../.tools/opentofu/1.11.6/tofu apply -auto-approve -var-file=tf.vars
```

## Proxmox Permissions

For the default native cloud-init mode on Proxmox VE 9 and newer, the stack needs 17 Proxmox VE privileges:

- VM scope, usually `/vms` with propagation because the source template and target VMIDs are environment-specific:
  `VM.Allocate`, `VM.Audit`, `VM.Clone`, `VM.Config.CDROM`, `VM.Config.Cloudinit`, `VM.Config.CPU`, `VM.Config.Disk`, `VM.Config.HWType`, `VM.Config.Memory`, `VM.Config.Network`, `VM.Config.Options`, `VM.PowerMgmt`, `VM.GuestAgent.Audit`
- Storage scope, at least `/storage/<pm_storage>`:
  `Datastore.Audit`, `Datastore.AllocateSpace`
- Node scope, `/nodes/<pm_node>`:
  `Sys.Audit`
- Network scope for the bridge used by the module, currently `vmbr0`:
  `SDN.Use`

On Proxmox VE 8 and older, replace `VM.GuestAgent.Audit` with `VM.Monitor` for guest-agent IP discovery. The count stays 17.

Telmate provider `3.0.2-rc04` performs a provider-wide minimum permission check by default. Its built-in list is broader than this module and checks privileges such as pool allocation, console access, system modification, and VM migration. The bundled stack disables that preflight check so Proxmox ACLs remain the source of enforcement:

```hcl
provider "proxmox" {
  pm_api_url          = var.pm_api_url
  pm_user             = var.pm_user
  pm_api_token_id     = var.pm_api_token_id
  pm_api_token_secret = var.pm_api_token_secret
  pm_tls_insecure     = var.pm_tls_insecure

  pm_minimum_permission_check = false
}
```

Example role split:

```bash
pveum role add InfraSkillVM --privs "VM.Allocate VM.Audit VM.Clone VM.Config.CDROM VM.Config.Cloudinit VM.Config.CPU VM.Config.Disk VM.Config.HWType VM.Config.Memory VM.Config.Network VM.Config.Options VM.PowerMgmt VM.GuestAgent.Audit"
pveum role add InfraSkillStorage --privs "Datastore.Audit Datastore.AllocateSpace"
pveum role add InfraSkillNode --privs "Sys.Audit"
pveum role add InfraSkillNetwork --privs "SDN.Use"

pveum aclmod /vms -user <user@realm> -role InfraSkillVM
pveum aclmod /storage/<pm_storage> -user <user@realm> -role InfraSkillStorage
pveum aclmod /nodes/<pm_node> -user <user@realm> -role InfraSkillNode
pveum aclmod /sdn/zones/localnetwork/<bridge> -user <user@realm> -role InfraSkillNetwork
```

Use propagation on VM and SDN scopes when the target objects live under those paths, for example `-propagate 1` on `/vms`. If you scope VM permissions tighter than `/vms`, grant the VM role to the source template VM and to the target VMID paths that this stack will create.

For privilege-separated API tokens, assign the same ACLs to the token as well, using `-token '<user@realm>!<tokenid>'`. Proxmox intersects token permissions with the backing user's permissions.

The module does not upload snippet files to Proxmox. If you use `cloud_init_delivery = "snippet"`, uploading rendered snippets is an out-of-band step. Upload through the Proxmox storage API or UI normally also needs `Datastore.AllocateTemplate` on `/storage/<pm_snippets_storage>`; direct filesystem or SFTP delivery depends on the host-level access method instead of PVE ACLs.

## Why This Works

- Module code is shared in `modules/ensure_vm`.
- State is isolated per stack directory.
- Generated artifacts are isolated by default in `stacks/<fleet-name>/.artifacts/`.
- The delivered key pair is `.artifacts/id_ed25519_tofu` and `.artifacts/id_ed25519_tofu.pub`; use it to log into the control node.
