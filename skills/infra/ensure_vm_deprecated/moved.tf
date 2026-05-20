# Keep existing ensure_vm state compatible after extracting resources into
# module.ensure_vm. This avoids unnecessary destroy/create during migration.
moved {
  from = tls_private_key.vm_ssh_key
  to   = module.ensure_vm.tls_private_key.vm_ssh_key
}

moved {
  from = local_file.ssh_private_key
  to   = module.ensure_vm.local_file.ssh_private_key
}

moved {
  from = local_file.user_data_snippet
  to   = module.ensure_vm.local_file.user_data_snippet
}

moved {
  from = proxmox_vm_qemu.vm
  to   = module.ensure_vm.proxmox_vm_qemu.vm
}

moved {
  from = local_file.ansible_inventory
  to   = module.ensure_vm.local_file.ansible_inventory
}
