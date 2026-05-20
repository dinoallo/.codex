resource "tls_private_key" "vm_ssh_key" {
  algorithm = "ED25519"
}

# Save the control login key pair under per-stack artifacts. The private key
# logs into the control node and, from that node, can reach all fleet nodes.
resource "local_file" "ssh_private_key" {
  content         = tls_private_key.vm_ssh_key.private_key_openssh
  filename        = local.ssh_private_key_path
  file_permission = "0600"
}

resource "local_file" "ssh_public_key" {
  content         = tls_private_key.vm_ssh_key.public_key_openssh
  filename        = local.ssh_public_key_path
  file_permission = "0644"
}
