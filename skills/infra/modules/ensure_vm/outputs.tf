output "vm_names" {
  description = "Names of the created VMs"
  value       = [for v in proxmox_vm_qemu.vm : v.name]
}

output "vm_vmid" {
  description = "VMIDs of the created VMs (provider attribute may be 'vmid' or 'id' depending on provider version)"
  value       = [for v in proxmox_vm_qemu.vm : try(v.vmid, v.id)]
}
