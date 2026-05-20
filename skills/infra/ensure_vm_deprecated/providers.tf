terraform {
  required_version = ">= 1.4.0"

  required_providers {
    # Primary Proxmox provider for VM management
    proxmox = {
      source  = "telmate/proxmox"
      version = "3.0.2-rc04"
    }
    # TLS provider to generate an SSH key pair
    tls = {
      source  = "hashicorp/tls"
      version = "4.0.5"
    }
    # Local provider to write the Ansible inventory file
    local = {
      source  = "hashicorp/local"
      version = "2.5.1"
    }
  }
}

provider "proxmox" {
  # Configuration is provided via variables below. You can also set these using
  # environment variables and/or a credentials file per your security practices.
  pm_api_url          = var.pm_api_url
  pm_user             = var.pm_user
  pm_api_token_id     = var.pm_api_token_id
  pm_api_token_secret = var.pm_api_token_secret
  pm_tls_insecure     = var.pm_tls_insecure
}
