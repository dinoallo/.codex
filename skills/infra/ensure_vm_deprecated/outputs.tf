output "vm_names" {
  description = "Names of the created VMs"
  value       = module.ensure_vm.vm_names
}

output "vm_vmid" {
  description = "VMIDs of the created VMs (provider attribute may be 'vmid' or 'id' depending on provider version)"
  value       = module.ensure_vm.vm_vmid
}
