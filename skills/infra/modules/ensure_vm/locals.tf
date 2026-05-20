locals {
  # Compute master/worker/control hostnames so existing master and worker
  # indices remain stable when a dedicated control node is added later.
  total_vm_count = var.vm_master_count + var.vm_worker_count + var.vm_control_count

  master_hostnames  = [for i in range(var.vm_master_count) : "${var.vm_name_prefix}-master-${i + 1}"]
  worker_hostnames  = [for i in range(var.vm_worker_count) : "${var.vm_name_prefix}-worker-${i + 1}"]
  control_hostnames = [for i in range(var.vm_control_count) : "${var.vm_name_prefix}-control-${i + 1}"]

  vm_hostnames = concat(local.master_hostnames, local.worker_hostnames, local.control_hostnames)
  vm_roles = concat(
    [for _ in local.master_hostnames : "master"],
    [for _ in local.worker_hostnames : "worker"],
    [for _ in local.control_hostnames : "control"]
  )

  master_vm_indices = tolist(range(0, var.vm_master_count))
  worker_vm_indices = tolist(range(var.vm_master_count, var.vm_master_count + var.vm_worker_count))
  default_control_vm_indices = tolist(
    var.vm_master_count > 0 ? [0] : []
  )
  control_vm_indices = var.vm_control_count > 0 ? tolist(
    range(var.vm_master_count + var.vm_worker_count, local.total_vm_count)
  ) : local.default_control_vm_indices

  has_control_node = length(local.control_vm_indices) > 0

  artifacts_dir_abs    = abspath(var.artifacts_dir)
  ssh_private_key_path = "${local.artifacts_dir_abs}/id_ed25519_tofu"
  ssh_public_key_path  = "${local.ssh_private_key_path}.pub"
  snippets_dir_path    = "${local.artifacts_dir_abs}/snippets"
  inventory_path       = "${local.artifacts_dir_abs}/ansible_inventory.ini"

  # Render one cloud-init user-data payload per VM hostname. Files are written
  # only when snippet delivery is enabled and uploaded to Proxmox out of band.
  cloud_init_config = [
    for i in range(local.total_vm_count) : templatefile("${path.module}/cloud_init.tpl", {
      ssh_public_key  = tls_private_key.vm_ssh_key.public_key_openssh
      hostname        = local.vm_hostnames[i]
      node_role       = local.vm_roles[i]
      is_control_node = contains(local.control_vm_indices, i)
      cloud_init_user = var.cloud_init_user
    })
  ]
}
