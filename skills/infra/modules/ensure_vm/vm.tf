resource "terraform_data" "topology_validation" {
  input = {
    master_count  = var.vm_master_count
    worker_count  = var.vm_worker_count
    control_count = var.vm_control_count
  }

  lifecycle {
    precondition {
      condition     = local.has_control_node
      error_message = "Invalid VM topology: create at least one master or one dedicated control node. Worker-only fleets are not supported."
    }
  }
}

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
  ciuser   = var.cloud_init_delivery == "native" && var.set_proxmox_ciuser ? var.cloud_init_user : null
  sshkeys  = tls_private_key.vm_ssh_key.public_key_openssh

  # Tell cloud-init to use DHCP
  ipconfig0 = "ip=dhcp"

  # Wait for clone operations to finish before continuing
  clone_wait = 30

  # Optional: set onboot (1 = start on host boot)
  onboot = true

  depends_on = [
    terraform_data.topology_validation,
    local_file.user_data_snippet
  ]

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

# Install the same control SSH key pair onto control nodes so the control host
# can initiate SSH sessions to every VM whose authorized_keys received the
# generated public key.
resource "terraform_data" "control_ssh_key_delivery" {
  count = length(local.control_vm_indices)

  input = {
    control_hostname = local.vm_hostnames[local.control_vm_indices[count.index]]
    control_ip       = proxmox_vm_qemu.vm[local.control_vm_indices[count.index]].default_ipv4_address
    all_node_ips     = proxmox_vm_qemu.vm[*].default_ipv4_address
    key_hash         = sha256(tls_private_key.vm_ssh_key.public_key_openssh)
  }

  triggers_replace = [
    proxmox_vm_qemu.vm[local.control_vm_indices[count.index]].id,
    proxmox_vm_qemu.vm[local.control_vm_indices[count.index]].default_ipv4_address,
    sha256(join(",", proxmox_vm_qemu.vm[*].default_ipv4_address)),
    sha256(tls_private_key.vm_ssh_key.public_key_openssh)
  ]

  connection {
    type        = "ssh"
    host        = proxmox_vm_qemu.vm[local.control_vm_indices[count.index]].default_ipv4_address
    user        = var.cloud_init_user
    private_key = tls_private_key.vm_ssh_key.private_key_openssh
    timeout     = "5m"
  }

  provisioner "remote-exec" {
    inline = [
      "set -eu",
      "mkdir -p ~/.ssh",
      "chmod 0700 ~/.ssh"
    ]
  }

  provisioner "file" {
    content     = tls_private_key.vm_ssh_key.private_key_openssh
    destination = "/tmp/infra_control_id_ed25519"
  }

  provisioner "file" {
    content     = tls_private_key.vm_ssh_key.public_key_openssh
    destination = "/tmp/infra_control_id_ed25519.pub"
  }

  provisioner "remote-exec" {
    inline = [
      "set -eu",
      "cat /tmp/infra_control_id_ed25519 > ~/.ssh/id_ed25519_tofu",
      "cat /tmp/infra_control_id_ed25519.pub > ~/.ssh/id_ed25519_tofu.pub",
      "chmod 0600 ~/.ssh/id_ed25519_tofu",
      "chmod 0644 ~/.ssh/id_ed25519_tofu.pub",
      "touch ~/.ssh/known_hosts",
      "chmod 0644 ~/.ssh/known_hosts",
      "for host in ${join(" ", proxmox_vm_qemu.vm[*].default_ipv4_address)}; do for attempt in 1 2 3 4 5; do ssh-keyscan -H \"$host\" >> ~/.ssh/known_hosts 2>/dev/null && break || sleep 3; done; done",
      "touch ~/.ssh/config",
      "sed -i '/# BEGIN infra-control-key/,/# END infra-control-key/d' ~/.ssh/config",
      "printf '%s\\n' '# BEGIN infra-control-key' 'Host *' '  IdentityFile ~/.ssh/id_ed25519_tofu' '  UserKnownHostsFile ~/.ssh/known_hosts' '# END infra-control-key' >> ~/.ssh/config",
      "chmod 0600 ~/.ssh/config",
      "rm -f /tmp/infra_control_id_ed25519 /tmp/infra_control_id_ed25519.pub"
    ]
  }

  depends_on = [
    proxmox_vm_qemu.vm,
    local_file.ssh_private_key,
    local_file.ssh_public_key
  ]
}

# Generate Ansible inventory file after VMs are created and have IPs
resource "local_file" "ansible_inventory" {
  filename = local.inventory_path

  content = templatefile("${path.module}/inventory.tpl", {
    controls             = [for i in local.control_vm_indices : proxmox_vm_qemu.vm[i].default_ipv4_address]
    masters              = [for i in local.master_vm_indices : proxmox_vm_qemu.vm[i].default_ipv4_address]
    workers              = [for i in local.worker_vm_indices : proxmox_vm_qemu.vm[i].default_ipv4_address]
    ssh_private_key_path = local.ssh_private_key_path
    cloud_init_user      = var.cloud_init_user
  })

  depends_on = [
    proxmox_vm_qemu.vm,
    terraform_data.control_ssh_key_delivery,
    local_file.ssh_private_key,
    local_file.ssh_public_key
  ]
}
