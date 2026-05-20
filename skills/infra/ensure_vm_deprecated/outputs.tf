output "vm_names" {
  description = "Names of the created VMs"
  value       = module.ensure_vm.vm_names
}

output "control_vm_names" {
  description = "Names of VMs acting as control nodes"
  value       = module.ensure_vm.control_vm_names
}

output "control_vm_ipv4_addresses" {
  description = "IPv4 addresses of VMs acting as control nodes"
  value       = module.ensure_vm.control_vm_ipv4_addresses
}

output "vm_vmid" {
  description = "VMIDs of the created VMs (provider attribute may be 'vmid' or 'id' depending on provider version)"
  value       = module.ensure_vm.vm_vmid
}

output "control_ssh_private_key_path" {
  description = "Path to the private key used to log into the control node"
  value       = module.ensure_vm.control_ssh_private_key_path
}

output "control_ssh_public_key_path" {
  description = "Path to the public key authorized on all fleet nodes"
  value       = module.ensure_vm.control_ssh_public_key_path
}
