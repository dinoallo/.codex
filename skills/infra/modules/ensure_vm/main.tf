/*
Reusable module for provisioning a Proxmox VM fleet.

This module is intentionally stack-agnostic. Caller stacks should provide:
- provider configuration
- auth and target variables
- per-stack artifacts path
*/
