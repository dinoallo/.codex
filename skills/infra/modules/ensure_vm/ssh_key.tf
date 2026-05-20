resource "tls_private_key" "vm_ssh_key" {
  algorithm = "ED25519"
}

# Save the private key under per-stack artifacts.
resource "local_file" "ssh_private_key" {
  content         = tls_private_key.vm_ssh_key.private_key_openssh
  filename        = local.ssh_private_key_path
  file_permission = "0600"
}
