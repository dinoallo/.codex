locals {
  # Compute master/worker counts and hostnames so VM names and inventory groups
  # remain stable as counts change.
  total_vm_count = var.vm_master_count + var.vm_worker_count

  vm_hostnames = concat(
    [for i in range(var.vm_master_count) : "${var.vm_name_prefix}-master-${i + 1}"],
    [for i in range(var.vm_worker_count) : "${var.vm_name_prefix}-worker-${i + 1}"]
  )

  artifacts_dir_abs    = abspath(var.artifacts_dir)
  ssh_private_key_path = "${local.artifacts_dir_abs}/id_ed25519_tofu"
  snippets_dir_path    = "${local.artifacts_dir_abs}/snippets"
  inventory_path       = "${local.artifacts_dir_abs}/ansible_inventory.ini"

  # Render one cloud-init user-data payload per VM hostname. Files are written
  # only when snippet delivery is enabled and uploaded to Proxmox out of band.
  cloud_init_config = [
    for i in range(local.total_vm_count) : templatefile("${path.module}/cloud_init.tpl", {
      ssh_public_key = tls_private_key.vm_ssh_key.public_key_openssh
      hostname       = local.vm_hostnames[i]
      cloud_init_user = var.cloud_init_user
    })
  ]
}
