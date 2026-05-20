output "vm_names" {
  description = "Names of the created VMs"
  value       = module.ensure_vm.vm_names
}

output "vm_vmid" {
  description = "VMIDs of the created VMs"
  value       = module.ensure_vm.vm_vmid
}
