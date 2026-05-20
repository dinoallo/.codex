variable "pm_api_url" {
  description = "Proxmox API URL, e.g. https://proxmox.example.com:8006/api2/json"
  type        = string
}

variable "pm_user" {
  description = "Proxmox user, e.g. 'root@pam' or service account"
  type        = string
  default     = ""
}

variable "pm_api_token_id" {
  description = "Proxmox API token id (format: 'user@realm!tokenid'). Can also be set via PM_API_TOKEN_ID env var."
  type        = string
  default     = ""
}

variable "pm_api_token_secret" {
  description = "Proxmox API token secret (the UUID-like secret). Prefer passing via environment or a secrets manager."
  type        = string
  sensitive   = true
  default     = ""
}

variable "pm_tls_insecure" {
  description = "Set to true to skip TLS verification (not recommended for production)."
  type        = bool
  default     = true
}

variable "pm_node" {
  description = "Target Proxmox node name where VMs will be created"
  type        = string
  default     = "pve"
}

variable "pm_storage" {
  description = "Proxmox storage to use for VM disks (e.g. local-lvm, local)"
  type        = string
  default     = "local-lvm"
}

variable "pm_snippets_storage" {
  description = "Proxmox storage containing cloud-init snippets referenced by cicustom. Only used when cloud_init_delivery is 'snippet'."
  type        = string
  default     = "local"
}

variable "cloud_init_delivery" {
  description = "How to deliver cloud-init user data. Use 'native' for least-privilege Proxmox cloud-init fields, or 'snippet' for cicustom user-data files."
  type        = string
  default     = "native"

  validation {
    condition     = contains(["native", "snippet"], var.cloud_init_delivery)
    error_message = "cloud_init_delivery must be either 'native' or 'snippet'."
  }
}

variable "cloud_init_user" {
  description = "Guest user configured through Proxmox cloud-init."
  type        = string
  default     = "root"
}

variable "vm_template" {
  description = "Clonable Proxmox template identifier accepted by the provider version in use (template name or VMID)."
  type        = string
  default     = "tf-ubuntu-template"
}

variable "vm_name_prefix" {
  description = "Prefix to use for VM names and hostnames."
  type        = string
  default     = "server"
}

variable "vm_master_count" {
  description = "Number of master VMs to create"
  type        = number
  default     = 1

  validation {
    condition     = var.vm_master_count >= 0 && floor(var.vm_master_count) == var.vm_master_count
    error_message = "vm_master_count must be a whole number greater than or equal to 0."
  }
}

variable "vm_worker_count" {
  description = "Number of worker VMs to create"
  type        = number
  default     = 2

  validation {
    condition     = var.vm_worker_count >= 0 && floor(var.vm_worker_count) == var.vm_worker_count
    error_message = "vm_worker_count must be a whole number greater than or equal to 0."
  }
}

variable "vm_control_count" {
  description = "Number of dedicated control VMs to create. Set to 0 to use the first master as the control node."
  type        = number
  default     = 0

  validation {
    condition     = var.vm_control_count >= 0 && floor(var.vm_control_count) == var.vm_control_count
    error_message = "vm_control_count must be a whole number greater than or equal to 0."
  }
}

variable "vm_memory_mb" {
  description = "Memory for each VM in MB"
  type        = number
  default     = 2048
}

variable "vm_cores" {
  description = "CPU cores per VM"
  type        = number
  default     = 2
}

variable "vm_disk_gb" {
  description = "Disk size (GB) to allocate for the new VM disk when cloning"
  type        = number
  default     = 0
}

variable "artifacts_dir" {
  description = "Directory where this stack writes generated artifacts (SSH key, inventory, and optional snippets). Relative paths are resolved from the caller stack."
  type        = string
  default     = ".artifacts"
}
