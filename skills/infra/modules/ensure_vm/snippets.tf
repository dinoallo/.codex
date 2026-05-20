// Render one local snippet file per VM only when cicustom snippet delivery is
// explicitly enabled. Native cloud-init delivery does not need snippet files.
resource "local_file" "user_data_snippet" {
  count           = var.cloud_init_delivery == "snippet" ? local.total_vm_count : 0
  filename        = "${local.snippets_dir_path}/${local.vm_hostnames[count.index]}_user_data.yml"
  content         = local.cloud_init_config[count.index]
  file_permission = "0644"

  depends_on = [local_file.ssh_private_key]
}
