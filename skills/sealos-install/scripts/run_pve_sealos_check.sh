#!/usr/bin/env bash
set -e
prompt_required() {
  local var_name="$1"
  local prompt="$2"
  if [[ -n "${!var_name:-}" ]]; then
    return
  fi
  if [[ ! -t 0 ]]; then
    echo "错误：缺少 ${var_name}，非交互模式下请通过环境变量传入。"
    exit 2
  fi
  local input=""
  while [[ -z "$input" ]]; do
    read -r -p "${prompt}: " input
  done
  printf -v "$var_name" '%s' "$input"
}

TARGET_IP="${TARGET_IP:-}"
PVE_ID="${PVE_ID:-}"

if [[ -z "$TARGET_IP" && -n "${IP:-}" ]]; then
  TARGET_IP="$IP"
fi
if [[ -z "$PVE_ID" && -n "${ID:-}" ]]; then
  PVE_ID="$ID"
fi

prompt_required TARGET_IP "目标 IP"
prompt_required PVE_ID "ID（用于主机名）"

SSH_USER="${SSH_USER:-sealos}"
SSH_PASS="${SSH_PASS:-1234}"
HOSTNAME_VALUE="${HOSTNAME_VALUE:-pve-${PVE_ID}}"
STATIC_URL="${STATIC_URL:-http://192.168.0.201:13600/make_static}"
ROOT_PUBLIC_KEY_PATH="${ROOT_PUBLIC_KEY_PATH:-$HOME/.ssh/id_rsa.pub}"
ROOT_IDENTITY_FILE="${ROOT_IDENTITY_FILE:-${ROOT_PUBLIC_KEY_PATH%.pub}}"
REQ_CPU="${REQ_CPU:-8}"
REQ_MEM_GB="${REQ_MEM_GB:-28}"
REQ_ROOT_GB="${REQ_ROOT_GB:-500}"

if [[ ! -r "$ROOT_PUBLIC_KEY_PATH" ]]; then
  echo "错误：无法读取 root 公钥文件：$ROOT_PUBLIC_KEY_PATH"
  exit 2
fi

ROOT_PUBLIC_KEY=$(awk 'NF {print; exit}' "$ROOT_PUBLIC_KEY_PATH")
if [[ -z "$ROOT_PUBLIC_KEY" ]]; then
  echo "错误：root 公钥文件为空：$ROOT_PUBLIC_KEY_PATH"
  exit 2
fi

if [[ ! -r "$ROOT_IDENTITY_FILE" ]]; then
  echo "错误：无法读取 root 登录私钥文件：$ROOT_IDENTITY_FILE"
  exit 2
fi

SSH_OPTS=(
  -o StrictHostKeyChecking=accept-new
  -o ConnectTimeout=10
  -o ServerAliveInterval=5
  -o ServerAliveCountMax=3
  -o LogLevel=ERROR
)

SSH_ENV=(env)
if [[ -n "${SSH_KEY_PATH:-}" ]]; then
  SSH_BASE=(ssh -i "$SSH_KEY_PATH")
elif command -v sshpass >/dev/null 2>&1; then
  SSH_BASE=(sshpass -p "$SSH_PASS" ssh)
else
  if ! command -v ssh >/dev/null 2>&1; then
    echo "错误：未找到 ssh。"
    exit 3
  fi
  ASKPASS_DIR=$(mktemp -d)
  ASKPASS_SCRIPT="$ASKPASS_DIR/askpass.sh"
  printf '#!/usr/bin/env bash\n%s\n' "echo \"$SSH_PASS\"" >"$ASKPASS_SCRIPT"
  chmod 700 "$ASKPASS_SCRIPT"
  SSH_ENV=(env SSH_ASKPASS="$ASKPASS_SCRIPT" SSH_ASKPASS_REQUIRE=force DISPLAY=1)
  SSH_BASE=(ssh)
  cleanup() {
    rm -rf "$ASKPASS_DIR"
  }
  trap cleanup EXIT
fi

SSH_TARGET="${SSH_USER}@${TARGET_IP}"
ROOT_SSH_TARGET="root@${TARGET_IP}"

REMOTE_CMD=$(printf "sudo -S -p '' bash -s -- %q %q %q %q %q %q" "$HOSTNAME_VALUE" "$STATIC_URL" "$ROOT_PUBLIC_KEY" "$REQ_CPU" "$REQ_MEM_GB" "$REQ_ROOT_GB")

set +e
{
  printf '%s\n' "$SSH_PASS"
  cat <<'REMOTE'
set -e
HOSTNAME_VALUE="${1:-}"
STATIC_URL="${2:-}"
ROOT_PUBLIC_KEY="${3:-}"
REQ_CPU="${4:-8}"
REQ_MEM_GB="${5:-28}"
REQ_ROOT_GB="${6:-500}"

if [[ -z "$HOSTNAME_VALUE" ]]; then
  echo "错误：主机名为空"
  exit 10
fi
if [[ -z "$STATIC_URL" ]]; then
  echo "错误：静态 IP URL 为空"
  exit 11
fi
if [[ -z "$ROOT_PUBLIC_KEY" ]]; then
  echo "错误：root 公钥为空"
  exit 12
fi

REPORT_PATH=/var/tmp/sealos-install-pve-preflight-report.txt
LOG_PATH=/var/tmp/sealos-install-pve-preflight.log

exec >>"$LOG_PATH" 2>&1

report() {
  printf '%s\n' "$*" >>"$REPORT_PATH"
}

get_disk() {
  local dev="$1"
  local disk
  disk=$(lsblk -no PKNAME "$dev" 2>/dev/null | head -n1 || true)
  if [[ -z "$disk" ]]; then
    disk=$(basename "$dev")
  fi
  echo "$disk"
}

get_partnum() {
  local dev="$1"
  local base
  base=$(basename "$dev")
  if [[ -e "/sys/class/block/$base/partition" ]]; then
    cat "/sys/class/block/$base/partition"
  fi
}

: > "$REPORT_PATH"

report "===PVE_SEALOS_CHECK_报告==="
report "时间: $(date -Iseconds)"
report "主机名_前: $(hostname)"

ROOT_SRC=$(findmnt -n -o SOURCE /)
ROOT_FSTYPE=$(findmnt -n -o FSTYPE /)
report "根分区源: $ROOT_SRC"
report "根分区类型: $ROOT_FSTYPE"

CPU_CORES=$(nproc)
MEM_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
MEM_GB=$(awk -v kb="$MEM_KB" 'BEGIN{printf "%.1f", kb/1024/1024}')
report "CPU核数: $CPU_CORES"
report "内存_GB: $MEM_GB"

ROOT_SIZE_BYTES_BEFORE=$(df -B1 --output=size / | tail -1 | tr -d ' ')
ROOT_SIZE_H_BEFORE=$(df -h --output=size / | tail -1 | tr -d ' ')
report "根分区大小_前: $ROOT_SIZE_H_BEFORE"

run_expand() {
  if [[ "$ROOT_SRC" == /dev/mapper/* ]]; then
    report "扩容模式: LVM"
    LV_PATH="$ROOT_SRC"
    VG_NAME=$(lvs --noheadings -o vg_name "$LV_PATH" | awk '{print $1}')
    if [[ -z "$VG_NAME" ]]; then
      report "扩容错误：无法解析 VG 名称"
      return 2
    fi

    PV_LIST=$(pvs --noheadings -o pv_name -S vgname="$VG_NAME" | awk '{print $1}')
    PV_COUNT=$(echo "$PV_LIST" | wc -w | awk '{print $1}')
    if [[ "$PV_COUNT" -ne 1 ]]; then
      report "扩容错误：VG 存在多个 PV"
      report "PV 列表: $PV_LIST"
      return 3
    fi

    PV_DEV=$(echo "$PV_LIST" | awk 'NR==1{print $1}')
    DISK=$(get_disk "$PV_DEV")
    PARTNUM=$(get_partnum "$PV_DEV")
    DISK_DEV="/dev/$DISK"
    report "PV设备: $PV_DEV"
    report "磁盘设备: $DISK_DEV"
    report "分区号: ${PARTNUM:-<无>}"

    if [[ -n "$PARTNUM" ]]; then
      if command -v growpart >/dev/null 2>&1; then
        growpart "$DISK_DEV" "$PARTNUM"
      elif command -v parted >/dev/null 2>&1; then
        parted -s "$DISK_DEV" "resizepart $PARTNUM 100%"
      else
        report "扩容错误：缺少 growpart/parted"
        return 4
      fi
      partprobe "$DISK_DEV" || true
    else
      report "分区扩容：跳过（整盘 PV）"
    fi

    pvresize "$PV_DEV"
    lvextend -r -l +100%FREE "$LV_PATH"
  else
    report "扩容模式: 非 LVM"
    if [[ "$ROOT_SRC" != /dev/* ]]; then
      report "扩容错误：不支持的根分区源"
      return 5
    fi

    DISK=$(get_disk "$ROOT_SRC")
    PARTNUM=$(get_partnum "$ROOT_SRC")
    DISK_DEV="/dev/$DISK"
    report "磁盘设备: $DISK_DEV"
    report "分区号: ${PARTNUM:-<无>}"

    if [[ -n "$PARTNUM" ]]; then
      if command -v growpart >/dev/null 2>&1; then
        growpart "$DISK_DEV" "$PARTNUM"
      elif command -v parted >/dev/null 2>&1; then
        parted -s "$DISK_DEV" "resizepart $PARTNUM 100%"
      else
        report "扩容错误：缺少 growpart/parted"
        return 6
      fi
      partprobe "$DISK_DEV" || true
    else
      report "分区扩容：跳过（整盘根分区）"
    fi

    if [[ "$ROOT_FSTYPE" == "xfs" ]]; then
      xfs_growfs /
    else
      resize2fs "$ROOT_SRC"
    fi
  fi
}

EXPAND_STATUS=0
if ! run_expand; then
  EXPAND_STATUS=1
fi
report "扩容状态: $EXPAND_STATUS"

# Hostname
if command -v hostnamectl >/dev/null 2>&1; then
  hostnamectl set-hostname "$HOSTNAME_VALUE"
else
  hostname "$HOSTNAME_VALUE"
  echo "$HOSTNAME_VALUE" >/etc/hostname
fi
report "主机名_后: $(hostname)"

ROOT_KEY_STATUS=0
mkdir -p /root/.ssh
chmod 700 /root/.ssh
touch /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
if ! grep -Fxq "$ROOT_PUBLIC_KEY" /root/.ssh/authorized_keys; then
  printf '%s\n' "$ROOT_PUBLIC_KEY" >>/root/.ssh/authorized_keys
fi
chown -R root:root /root/.ssh
report "root公钥写入: PASS"

# Static IP script
set +e
STATIC_IP_RESP=$(curl -sS -X POST "$STATIC_URL" 2>&1)
STATIC_IP_RC=$?
set -e
report "静态IP返回码: $STATIC_IP_RC"
if [[ -n "$STATIC_IP_RESP" ]]; then
  report "静态IP响应: $STATIC_IP_RESP"
fi

ROOT_SIZE_BYTES_AFTER=$(df -B1 --output=size / | tail -1 | tr -d ' ')
ROOT_SIZE_H_AFTER=$(df -h --output=size / | tail -1 | tr -d ' ')
report "根分区大小_后: $ROOT_SIZE_H_AFTER"

REQ_MEM_KB=$((REQ_MEM_GB*1024*1024))
REQ_ROOT_BYTES=$((REQ_ROOT_GB*1024*1024*1024))

CPU_OK=$([[ "$CPU_CORES" -ge "$REQ_CPU" ]] && echo PASS || echo FAIL)
MEM_OK=$([[ "$MEM_KB" -ge "$REQ_MEM_KB" ]] && echo PASS || echo FAIL)
ROOT_OK=$([[ "$ROOT_SIZE_BYTES_AFTER" -ge "$REQ_ROOT_BYTES" ]] && echo PASS || echo FAIL)

report "检查CPU: $CPU_OK"
report "检查内存: $MEM_OK"
report "检查根分区: $ROOT_OK"

report "-- IP地址 --"
ip -4 addr show >>"$REPORT_PATH"

report "-- 磁盘占用 --"
df -h / >>"$REPORT_PATH"

report "-- 块设备 --"
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINT >>"$REPORT_PATH"

report "修复建议:"
if [[ "$CPU_OK" == "FAIL" ]]; then
  report "- 将 vCPU 提升到 >= ${REQ_CPU}。"
fi
if [[ "$MEM_OK" == "FAIL" ]]; then
  report "- 将内存提升到 >= ${REQ_MEM_GB}G。"
fi
if [[ "$ROOT_OK" == "FAIL" ]]; then
  report "- 将虚拟磁盘扩容到 >= ${REQ_ROOT_GB}G 后重跑。"
fi
if [[ "$EXPAND_STATUS" -ne 0 ]]; then
  report "- 根分区扩容失败；检查 growpart/parted、pvresize、lvextend 的日志。"
fi
if [[ "$STATIC_IP_RC" -ne 0 ]]; then
  report "- 静态 IP 脚本失败；检查 ${STATIC_URL}。"
fi

STATIC_IPS=$(ip -4 -o addr show scope global | awk '{print $4}' | sed 's#/.*##' | paste -sd "," -)
if [[ -z "$STATIC_IPS" ]]; then
  STATIC_IPS="UNKNOWN"
fi
EXPAND_OK=$([[ "$EXPAND_STATUS" -eq 0 ]] && echo PASS || echo FAIL)
ROOT_KEY_OK=$([[ "$ROOT_KEY_STATUS" -eq 0 ]] && echo PASS || echo FAIL)

cat >"$REPORT_PATH" <<EOF
===PVE_SEALOS_CHECK_报告===
时间: $(date -Iseconds)
主机名: $(hostname)
检查CPU: $CPU_OK
检查内存: $MEM_OK
检查根分区: $ROOT_OK
静态IP: $STATIC_IPS
扩容检查: $EXPAND_OK
root公钥写入: $ROOT_KEY_OK
===结束===
EOF

sync
sleep 1
reboot
REMOTE
} | "${SSH_ENV[@]}" "${SSH_BASE[@]}" "${SSH_OPTS[@]}" "$SSH_TARGET" "$REMOTE_CMD"
SSH_RC=$?
set -e

ONLINE=0
set +e
for _ in $(seq 1 60); do
  "${SSH_ENV[@]}" "${SSH_BASE[@]}" "${SSH_OPTS[@]}" "$SSH_TARGET" "echo online" >/dev/null 2>&1
  if [[ $? -eq 0 ]]; then
    ONLINE=1
    break
  fi
  sleep 5
done
set -e

if [[ "$ONLINE" -ne 1 ]]; then
  echo "错误：主机未恢复在线，请检查 IP/控制台。"
  exit 4
fi

ROOT_LOGIN_OK=0
"${SSH_ENV[@]}" ssh "${SSH_OPTS[@]}" \
  -i "$ROOT_IDENTITY_FILE" \
  -o BatchMode=yes \
  -o IdentitiesOnly=yes \
  -o PasswordAuthentication=no \
  "$ROOT_SSH_TARGET" "true" >/dev/null 2>&1 || ROOT_LOGIN_OK=1

"${SSH_ENV[@]}" "${SSH_BASE[@]}" "${SSH_OPTS[@]}" "$SSH_TARGET" "cat /var/tmp/sealos-install-pve-preflight-report.txt"

if [[ "$ROOT_LOGIN_OK" -eq 0 ]]; then
  echo "root免密登录: PASS"
else
  echo "root免密登录: FAIL"
  exit 5
fi
