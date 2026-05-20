#cloud-config
# Rendered locally by OpenTofu when cloud_init_delivery = "snippet".
# Upload this file to Proxmox snippets storage and reference it via cicustom.

hostname: ${hostname}
fqdn: ${hostname}
manage_etc_hosts: false
user: ${cloud_init_user}
write_files:
  - path: /etc/infra-node-role
    permissions: "0644"
    content: |
      ${node_role}
  - path: /etc/infra-control-node
    permissions: "0644"
    content: |
      ${is_control_node}
disable_root: false
ssh_authorized_keys:
  - ${ssh_public_key}
chpasswd:
  expire: false
package_update: true
package_upgrade: true

# Ensure cloned machines regenerate unique SSH host keys.
ssh_deletekeys: true
