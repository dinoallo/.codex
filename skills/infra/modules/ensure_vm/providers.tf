terraform {
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
    # Local provider to write inventory and optional rendered snippet files
    local = {
      source  = "hashicorp/local"
      version = "2.5.1"
    }
  }
}
