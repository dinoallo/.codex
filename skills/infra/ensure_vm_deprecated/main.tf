module "ensure_vm" {
  source = "../modules/ensure_vm"

  pm_api_url          = var.pm_api_url
  pm_user             = var.pm_user
  pm_api_token_id     = var.pm_api_token_id
  pm_api_token_secret = var.pm_api_token_secret
  pm_tls_insecure     = var.pm_tls_insecure
  pm_node             = var.pm_node
  pm_storage          = var.pm_storage
  pm_snippets_storage = var.pm_snippets_storage
  cloud_init_delivery = var.cloud_init_delivery
  cloud_init_user     = var.cloud_init_user
  set_proxmox_ciuser  = var.set_proxmox_ciuser
  vm_template         = var.vm_template
  vm_name_prefix      = var.vm_name_prefix
  vm_master_count     = var.vm_master_count
  vm_worker_count     = var.vm_worker_count
  vm_control_count    = var.vm_control_count
  vm_memory_mb        = var.vm_memory_mb
  vm_cores            = var.vm_cores
  vm_disk_gb          = var.vm_disk_gb
  artifacts_dir       = var.artifacts_dir
}
