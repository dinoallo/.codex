// ---- VM resources: create N clones ----
resource "proxmox_vm_qemu" "vm" {
  count       = local.total_vm_count
  name        = local.vm_hostnames[count.index]
  target_node = var.pm_node
  clone       = var.vm_template
  full_clone  = false
  os_type     = "cloud-init"
  boot        = "order=scsi0;net0"

  # 1. Enable the QEMU Guest Agent
  agent = 1

  # Native cloud-init fields preserve least-privilege provisioning. Snippet
  # delivery is opt-in for custom user-data and requires pre-uploaded snippets.
  cicustom = var.cloud_init_delivery == "snippet" ? "user=${var.pm_snippets_storage}:snippets/${local.vm_hostnames[count.index]}_user_data.yml" : null
  ciuser   = var.cloud_init_user
  sshkeys  = tls_private_key.vm_ssh_key.public_key_openssh

  # Tell cloud-init to use DHCP
  ipconfig0 = "ip=dhcp"

  # Wait for clone operations to finish before continuing
  clone_wait = 30

  # Optional: set onboot (1 = start on host boot)
  onboot = true

  depends_on = [local_file.user_data_snippet]

  # Provider versions may normalize empty tags differently ("" vs " " vs null).
  # Ignore tag drift to avoid unnecessary VM updates.
  lifecycle {
    ignore_changes = [tags]
  }

  # Basic hardware sizing
  cpu {
    cores   = var.vm_cores
    sockets = 1
  }
  memory = var.vm_memory_mb

  scsihw = "virtio-scsi-single"

  # Explicit disks block: leave scsi0 unmanaged so the linked clone keeps the
  # template's existing boot disk layout from the chosen template identifier.
  disks {
    ide {
      ide1 {
        cloudinit {
          storage = var.pm_storage
        }
      }
    }
    scsi {
      # Do not manage scsi0 here (inherit from template). This tells the provider
      # to leave scsi0 alone so the clone uses the template's disk.
      scsi0 {
        ignore = true
      }

      # Conditionally add scsi1 when vm_disk_gb > 0
      dynamic "scsi1" {
        for_each = var.vm_disk_gb > 0 ? [1] : []
        content {
          disk {
            iothread = true
            storage  = var.pm_storage
            size     = var.vm_disk_gb
          }
        }
      }
    }
  }

  # Simple network config - attach to bridge vmbr0 using virtio
  network {
    id     = 0
    model  = "virtio"
    bridge = "vmbr0"
  }
}

# Generate Ansible inventory file after VMs are created and have IPs
resource "local_file" "ansible_inventory" {
  filename = local.inventory_path

  content = templatefile("${path.module}/inventory.tpl", {
    masters              = slice(proxmox_vm_qemu.vm.*.default_ipv4_address, 0, var.vm_master_count)
    workers              = slice(proxmox_vm_qemu.vm.*.default_ipv4_address, var.vm_master_count, local.total_vm_count)
    ssh_private_key_path = local.ssh_private_key_path
    cloud_init_user      = var.cloud_init_user
  })

  depends_on = [
    proxmox_vm_qemu.vm,
    local_file.ssh_private_key
  ]
}
