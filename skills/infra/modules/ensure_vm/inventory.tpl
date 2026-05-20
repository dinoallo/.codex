[masters]
# First master (one entry) is separated out below as a special role.
# The rest of the masters (if any) are listed in `other_masters`.
${masters[0]} ansible_user=${cloud_init_user}

[other_masters]
# Any additional masters (excluding the first) go here.
%{ for ip in masters ~}
%{ if ip != masters[0] ~}
${ip} ansible_user=${cloud_init_user}
%{ endif ~}
%{ endfor ~}

[masters:children]
first_master
other_masters

[first_master]
# Group containing only the very first master
${masters[0]} ansible_user=${cloud_init_user}

[workers]
# All worker nodes
%{ for ip in workers ~}
${ip} ansible_user=${cloud_init_user}
%{ endfor ~}

[all:vars]
# Tell Ansible to use the private key we generated
ansible_ssh_private_key_file = ${ssh_private_key_path}
ansible_python_interpreter = /usr/bin/python3
ansible_ssh_common_args = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
