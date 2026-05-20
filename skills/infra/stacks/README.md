# Stack Layout

Each subdirectory under `stacks/` is an independent root module with its own state and fleet configuration.

## Create A New Fleet Stack

1. Copy `_template` to a new folder:

```bash
cp -R stacks/_template stacks/<fleet-name>
```

2. Edit `stacks/<fleet-name>/tf.vars` (or another `*.tfvars` file) with your prefix, counts, and Proxmox settings.
3. Keep `cloud_init_delivery = "native"` for least-privilege provisioning. Use `cloud_init_delivery = "snippet"` only when custom first-boot user-data cannot be baked into the template.
4. Run OpenTofu in that folder:

```bash
cd stacks/<fleet-name>
../../.tools/opentofu/1.11.6/tofu init
../../.tools/opentofu/1.11.6/tofu apply -auto-approve -var-file=tf.vars
```

## Why This Works

- Module code is shared in `modules/ensure_vm`.
- State is isolated per stack directory.
- Generated artifacts are isolated by default in `stacks/<fleet-name>/.artifacts/`.
