output "vm_names" {
  description = "Names of the created VMs"
  value       = [for v in proxmox_vm_qemu.vm : v.name]
}

output "control_vm_names" {
  description = "Names of VMs acting as control nodes. When vm_control_count is 0, this is the first master."
  value       = [for i in local.control_vm_indices : proxmox_vm_qemu.vm[i].name]
}

output "control_vm_ipv4_addresses" {
  description = "IPv4 addresses of VMs acting as control nodes."
  value       = [for i in local.control_vm_indices : proxmox_vm_qemu.vm[i].default_ipv4_address]
}

output "vm_vmid" {
  description = "VMIDs of the created VMs (provider attribute may be 'vmid' or 'id' depending on provider version)"
  value       = [for v in proxmox_vm_qemu.vm : try(v.vmid, v.id)]
}

output "control_ssh_private_key_path" {
  description = "Path to the private key used to log into the control node."
  value       = local.ssh_private_key_path
}

output "control_ssh_public_key_path" {
  description = "Path to the public key authorized on all fleet nodes."
  value       = local.ssh_public_key_path
}
