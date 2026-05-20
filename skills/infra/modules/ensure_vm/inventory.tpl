[control]
%{ for ip in controls ~}
${ip} ansible_user=${cloud_init_user}
%{ endfor ~}

[masters]
%{ for ip in masters ~}
${ip} ansible_user=${cloud_init_user}
%{ endfor ~}

[other_masters]
# Any additional masters (excluding the first) go here.
%{ for index, ip in masters ~}
%{ if index > 0 ~}
${ip} ansible_user=${cloud_init_user}
%{ endif ~}
%{ endfor ~}

[first_master]
# Group containing only the very first master.
%{ if length(masters) > 0 ~}
${masters[0]} ansible_user=${cloud_init_user}
%{ endif ~}

[workers]
# All worker nodes.
%{ for ip in workers ~}
${ip} ansible_user=${cloud_init_user}
%{ endfor ~}

[all_nodes:children]
control
masters
first_master
other_masters
workers

[all:vars]
# This key logs into the control node and can reach all fleet nodes from there.
ansible_ssh_private_key_file = ${ssh_private_key_path}
ansible_python_interpreter = /usr/bin/python3
ansible_ssh_common_args = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
