---
name: sealos-install
description: 使用 ID、IP 和下载包矩阵安装、重跑检查或验收 Sealos Pro/OSS Cloud。内置 PVE/Ubuntu 主机准备流程，默认 SSH 账号密码为 sealos/1234；下载安装基础包，执行 sealos-pro.sh/sealos-oss.sh install，执行 info，本地用 cert.sh 强制信任浏览器证书作为每次最终成功报告门禁，支持增量包 sealos run，最终验证 info、离线镜像、集群健康和 URI 可达性，最终报告明文输出 info 登录用户名/密码，禁止执行 sealos reset。
---

# Sealos Install

当用户需要安装、验证或输出 Sealos Pro/OSS Cloud 离线包部署报告时，使用这个 skill。

## 必填输入

正常入口只需要用户提供这些输入：

| 输入 | 含义 | 环境变量别名 |
|---|---|---|
| ID | PVE ID，用于生成默认主机名 `pve-${ID}` | `ID` 或 `PVE_ID` |
| IP | 目标 Linux 主机 IP | `IP` 或 `TARGET_IP` |
| 下载包矩阵 | 基础包 URL，以及可选增量包 | 用户提供的表格或列表 |

默认不要询问 SSH 账号密码，直接使用：

| 字段 | 默认值 |
|---|---|
| SSH 用户 | `sealos` |
| SSH 密码 | `1234` |
| 主机名 | `pve-${ID}` |
| 静态 IP URL | `http://192.168.0.201:13600/make_static` |
| root 公钥 | `~/.ssh/id_rsa.pub` |
| root 私钥 | `~/.ssh/id_rsa` |
| 最低 CPU | `8` |
| 最低内存 | `28G` |
| 最低根分区 | `500G` |

只有用户明确要覆盖默认值，或默认本地 key 文件不可读时，才询问这些可选值。

## 下载包矩阵

如果用户尚未提供下载包矩阵，需要询问。基础包必须且只能有一个：`sealos-pro` 或 `sealos-oss`。增量包可选，在基础包安装完成后执行。

| 组件 | 必填 | 版本 | 架构 | 下载 URL | 运行目标 | 校验值 | 状态 | 备注 |
|---|---|---|---|---|---|---|---|---|
| sealos-pro base | 二选一 |  |  |  | 本地脚本目录 |  | 缺失 | 基础包必须且只能有一个 |
| sealos-oss base | 二选一 |  |  |  | 本地脚本目录 |  | 缺失 | 基础包必须且只能有一个 |
| sealos-admin | 可选 |  |  |  | 本地路径或镜像引用 |  | 跳过 | 基础包安装后用 `sealos run` 执行 |
| sealos-registry | 可选 |  |  |  | 本地路径或镜像引用 |  | 跳过 | 基础包安装后用 `sealos run` 执行 |
| aiproxy | 可选 |  |  |  | 本地路径或镜像引用 |  | 跳过 | 基础包安装后用 `sealos run` 执行 |
| dataflow | 可选 |  |  |  | 本地路径或镜像引用 |  | 跳过 | 基础包安装后用 `sealos run` 执行 |
| devbox | 可选 |  |  |  | 本地路径或镜像引用 |  | 跳过 | 基础包安装后用 `sealos run` 执行 |
| kite | 可选 |  |  |  | 本地路径或镜像引用 |  | 跳过 | 基础包安装后用 `sealos run` 执行 |
| sealaf | 可选 |  |  |  | 本地路径或镜像引用 |  | 跳过 | 基础包安装后用 `sealos run` 执行 |

矩阵规则：

- `下载 URL` 是目标主机上的下载来源。
- `运行目标` 是下载后用于 install/run 命令的本地包路径、解压目录或镜像引用。
- 如果 `运行目标` 为空，就根据目标主机上下载后的产物推导。
- 基础包的 `运行目标` 必须能解析到包含 `./sealos-pro.sh` 或 `./sealos-oss.sh` 的目录。
- 增量包在基础包安装成功后执行 `sealos run <运行目标>`。
- 如果 URL 含临时签名或 token，报告和最终回复中必须脱敏。

## 内置 PVE 准备

安装 Sealos Cloud 前，执行内置 PVE/Ubuntu 主机准备流程；只有用户明确说明已通过时才记录为已通过。

内置脚本是：

```bash
<this-skill>/scripts/run_pve_sealos_check.sh
```

它通过 SSH 准备并校验目标主机：

1. 使用必填 IP 和 ID，默认主机名为 `pve-${ID}`。
2. 默认使用 SSH 账号密码 `sealos/1234`、默认静态 IP URL、默认 root key 路径、默认 CPU/内存/根分区阈值，除非用户明确覆盖。
3. 尽可能远程扩容根分区，设置主机名，写入本机 root 公钥，调用静态 IP API，重启并等待恢复。
4. 验证本机能免密登录 `root@目标 IP`。
5. 输出远端报告 `/var/tmp/sealos-install-pve-preflight-report.txt`，并把目标 IP、主机名、root SSH 状态和准备结果带入安装上下文。

不要调用独立 PVE skill；相关逻辑已经内置在本 skill 中。

## 硬边界

- 在 IP 指向的目标 Linux 主机上执行安装。
- 永远不要执行 `sealos reset`。
- 开始前只询问缺失的 ID、IP、下载包矩阵。除非用户要覆盖默认值，或默认 key 文件不可读，否则不要询问 SSH 账号密码、主机名、静态 IP URL、root key 路径或资源阈值。
- 不要根据记忆推断包类型。必须从唯一基础包行确定 Pro/OSS，并在下载/解压后确认对应脚本存在。
- 证书信任是每次执行 `sealos-install` 的最终成功门禁。只要本次目标包含安装、重跑、继续安装、增量包、验收、重新检查或输出最终报告，就必须先执行对应 `info` 命令，再用必需的 `cert.sh` 命令在本地信任浏览器证书；确认信任成功后，再执行最终 `info` 命令，并把最终输出写入报告。
- 只从基础包目录里的本地文件判断配置模式：
  - 如果存在 `sealos.env`，使用旧版 env 模式。
  - 否则如果存在 `values/global.yaml`，使用 values 模式。
  - 如果二者都不存在，停止并报告基础包目录无效。
- 如果 `sealos.env` 和 `values/global.yaml` 同时存在，使用旧版 env 模式，并说明选择原因是存在 `sealos.env`。
- 最终报告必须明文输出 `sealos info` 中用于登录 Sealos Cloud 的用户名和密码，方便用户登录。下载 URL 中的临时签名、token、key、非登录密钥仍然必须脱敏。

## 交互输入规则

必须交互的点：

- 如果缺少 ID，询问 ID。
- 如果缺少 IP，询问 IP。
- 如果缺少下载包矩阵，询问下载包矩阵。
- 如果矩阵里不是“刚好一个基础包”，要求用户修正矩阵。
- 如果基础包目录里同时存在 `./sealos-pro.sh` 和 `./sealos-oss.sh`，按矩阵里选择的基础包类型执行；如果选中的脚本不存在，则基础包检查失败。
- 登录后如果 `hostname -I` 返回多个可能的 IPv4 地址，优先使用用户提供的 IP。只有主机报告了另一个可达 IP，且继续使用用户 IP 明显会导致域名错误时，才询问用户。

非交互自动化环境必须提前提供这些值。缺少必填数据时，停止并给出明确缺失提示，不要猜测。

## Linux 兼容性

- 这些安装脚本面向 Linux。
- 优先使用常见 Linux 主机上的 POSIX/GNU 兼容命令。
- 避免 BSD 专属参数、交互式编辑器，以及对 macOS 路径的假设。
- 执行 install 或 info 前，先确认目标脚本存在，并且可执行或可用 `bash` 运行。

## 域名规则

安装时根据用户提供的 IP 推导 Sealos Cloud 预期域名：

1. 域名格式为 `<ip>.nip.io`。
2. 将该域名与基础包当前配置对比。
3. 安装前报告不一致项。只有用户明确要求修改配置时，才编辑配置文件。

## 浏览器证书信任

证书信任不是可选优化，而是最终成功报告的强制门禁。每次执行本 skill，只要准备输出成功、继续安装、重跑验证、执行增量包或生成最终报告，都必须执行本节逻辑。

1. 无论本次是否重新执行基础包 `install`，都先执行匹配的 `info` 命令。
2. 从 `info` 输出中解析 Cloud HTTPS URL。如果 `info` 没有暴露可用 URL，则回退为 `https://<IP>.nip.io:443`。
3. 在本地执行下面的命令，不要在目标主机上执行：

   ```bash
   curl https://objectstorageapi.hzh.sealos.run/paxilf30-static/cert.sh | bash -s -- --mode auto "<cloud-https-url>"
   ```

   Example:

   ```bash
   curl https://objectstorageapi.hzh.sealos.run/paxilf30-static/cert.sh | bash -s -- --mode auto "https://192.168.10.70.nip.io:443"
   ```

4. 如果退出码非 0，记为 `Certificate trust: FAIL`，并在最终成功报告前停止。
5. 不允许因为“以前执行过”“证书看起来已存在”“本次只是重跑检查”“本次只跑增量包”跳过该命令；`cert.sh --mode auto` 需要按幂等动作重新执行。
6. 证书信任成功后，再次执行最终匹配的 `info` 命令，并在报告中输出最终 `sealos info` 结果。

## 执行流程

1. 如果尚未提供，只收集 ID、IP 和下载包矩阵。
2. 使用默认值执行内置 PVE 准备流程；只有用户明确说明已通过时，才记录为 `已通过`。
3. 把基础包 URL 下载到目标主机。如提供校验值，则执行校验。
4. 需要时解压基础包，然后定位基础包目录和匹配脚本：
   - Pro: `./sealos-pro.sh`
   - OSS: `./sealos-oss.sh`
5. 执行 `pwd`、`ls -la`，并根据 `sealos.env` / `values/global.yaml` 判断配置模式。只读取匹配的 reference 文件。
6. 使用用户提供的 IP 推导 `<ip>.nip.io`，并与当前配置对比。除非用户明确要求，否则不要编辑文件。
7. 执行匹配的基础包安装命令：
   - Pro: `./sealos-pro.sh install`
   - OSS: `./sealos-oss.sh install`
8. 执行匹配的安装后 info 命令：
   - Pro: `./sealos-pro.sh info`
   - OSS: `./sealos-oss.sh info`
9. 将 `info` 输出解析成表格。用于登录 Sealos Cloud 的用户名和密码必须明文输出；下载 URL 签名、token、key、非登录密钥和 URI 内嵌凭据仍然必须脱敏。
10. 执行 **浏览器证书信任** 一节里的本地证书信任命令，并确认成功。
11. 再次执行匹配的最终 info 命令，并把最终输出用于报告：
   - Pro: `./sealos-pro.sh info`
   - OSS: `./sealos-oss.sh info`
12. 如果 `crictl` 可用，验证当前运行镜像都来自离线 registry。离线 registry 允许两种前缀：
   - `sealos.hub:5000/`
   - `hub.<cloudDomain>/`，其中 `<cloudDomain>` 必须来自最终 `info` 输出、基础包配置或集群 `sealos-config.cloudDomain`，使用裸域名，不包含协议和端口，不能手写猜测。

   ```bash
   CLOUD_DOMAIN="<cloudDomain>"
   crictl images | awk -v domain="${CLOUD_DOMAIN}" '
     NR > 1 {
       image=$1
       hub_host="hub." domain
       allowed_hub_domain=(domain != "" && (image == hub_host || index(image, hub_host "/") == 1))
       if (image !~ /^sealos\.hub:5000(\/|$)/ && !allowed_hub_domain) {
         print image
       }
     }
   ' | sort -u
   ```

   - 如果命令没有输出，离线镜像校验通过。
   - 如果有输出，报告不合规镜像仓库，并将部署视为未完全离线。
   - 如果拿不到 `<cloudDomain>`，只能按 `sealos.hub:5000/` 校验；报告中将 `hub.<domain>` 兼容项标记为 `WARN` 或 `N/A`，并说明缺少 domain 来源。
   - 不为 Kubernetes、CNI、ingress、应用、监控或包辅助镜像添加例外；所有运行镜像仓库都必须使用 `sealos.hub:5000/` 或 `hub.<cloudDomain>/` 前缀。
13. 对每个提供了 `下载 URL` 或 `运行目标` 的增量包：
   - 如果提供 URL，则下载并校验。
   - 解析 `运行目标`。
   - 执行 `sealos run <运行目标>`。
   - 在具备足够 namespace/resource 信息时校验组件健康。
   - 重新执行离线镜像校验。
14. 如果执行过任何增量包、重跑检查或继续安装动作，必须再次执行 **浏览器证书信任** 一节里的本地证书信任命令；成功后再次执行最终 info，确保最终报告使用信任后的 info 输出。
15. 只有 `kubectl` 已配置时才检查集群健康，否则标记为 `N/A`。
16. 使用最终 info 输出做 URI 检查。
17. 生成安装报告，包含输入摘要、PVE 准备结果、基础包安装结果、证书信任结果、增量包结果、最终 `info` 输出表、当前离线镜像校验、集群健康和 URI 可达性。

## 报告

始终输出简洁的表格报告，必须包含：

- 输入摘要：ID、IP、选择的基础包，以及默认 SSH 用户。
- 下载包矩阵：每个基础包/增量包行的下载、校验、安装/运行状态和备注。
- PVE 准备：状态、目标 IP/主机名、root SSH 状态和报告路径。
- 基础包：Pro/OSS、版本（如可得）、基础包目录、配置模式、cloud domain、cloud port。
- 证书信任：本地 cert.sh 命令、目标 HTTPS URL、退出状态和备注。
- 增量包：`sealos run` 结果、组件健康结果、离线镜像结果和备注。
- Info 输出：最终 `./sealos-pro.sh info` 或 `./sealos-oss.sh info` 的表格。登录用户名和登录密码必须明文输出；下载 URL 签名、token、key、非登录密钥和 URI 内嵌凭据仍需脱敏。
- 集群：可用时输出 `kubectl get nodes -o wide`、非 Running/非 Succeeded Pod、未 Ready Deployment。
- 离线镜像：当前 `crictl images` 前缀检查结果，明确列出采用的合法前缀：`sealos.hub:5000/` 和本次解析到的 `hub.<cloudDomain>/`。
- URI 检查：最终 info 输出中的每个 `PublishAddr`。

使用这个报告表：

| 检测项 | 结果 | 依据 | 建议 |
|---|---|---|---|
| 输入 | PASS/FAIL | ID/IP/下载包矩阵 |  |
| PVE 准备 | PASS/FAIL/N/A | 内置 PVE 报告 |  |
| 基础包下载 | PASS/FAIL | URL/校验值/解压目录 |  |
| 配置模式 | PASS/FAIL | sealos.env or values/global.yaml |  |
| 域名配置 | PASS/WARN/FAIL | IP-derived domain and config value |  |
| 基础包安装 | PASS/FAIL | sealos-pro.sh/sealos-oss.sh install |  |
| 证书信任 | PASS/FAIL | cert.sh --mode auto 结果 |  |
| 增量包 | PASS/WARN/FAIL/N/A | sealos run 结果 |  |
| Info 命令 | PASS/WARN/FAIL | sealos-pro.sh/sealos-oss.sh info |  |
| 离线镜像 | PASS/WARN/FAIL/N/A | crictl images 前缀检查；合法前缀为 sealos.hub:5000/ 与 hub.<cloudDomain>/ |  |
| 集群健康 | PASS/WARN/FAIL/N/A | kubectl 检查 |  |
| URI 可达性 | PASS/WARN/FAIL/N/A | curl 检查 |  |

URI 检查规则：

- 对每个 HTTP(S) URI 执行 `curl -k -I --connect-timeout 10 --max-time 20 <uri>`。
- 2xx/3xx 视为可达；401/403 视为可达但受保护；4xx/5xx 和连接错误视为失败。
- 如果能安全自动化浏览器或应用登录，可以用发现的登录凭据尝试登录；报告中需要明文给出登录用户名和密码。
- 如果无法可靠自动化登录，不要编造成功；报告 URI 可达，并标记为 `需要人工验证登录`。
- 对非 HTTP 地址，说明为什么跳过自动 URI/登录测试。

建议报告结构：

```markdown
## Sealos 安装报告

- 总体结果：PASS|WARN|FAIL
- 基础包安装：PASS|FAIL
- 证书信任：PASS|FAIL
- 增量包：PASS|WARN|FAIL|N/A
- 离线镜像校验：PASS|WARN|FAIL|N/A
- 集群健康：PASS|WARN|FAIL|N/A
- URI 可达性：PASS|WARN|FAIL|N/A

### 输入
| ID | IP | 基础包 | SSH 用户 |
| --- | --- | --- | --- |

### 下载包矩阵
<下载包矩阵，URL 敏感查询参数需脱敏>

### PVE 准备
<内置 PVE 准备结果摘要和报告路径>

### 安装结果
<基础包和增量包结果表>

### 证书信任
<本地 cert.sh 命令、HTTPS URL 和执行结果>

### 集群
<节点、Pod、Deployment 摘要>

### 检查摘要
<检测项表格>

### Info 输出
<最终 ./sealos-pro.sh info 或 ./sealos-oss.sh info 的表格；登录用户名和密码明文输出，其它非登录密钥脱敏>

### URI 检查
| 名称 | 用户 | URL | 可达性 | 登录 |
| --- | --- | --- | --- | --- |
```

## 模式参考

- 旧版 `sealos.env` 模式读取 `references/sealos-env.md`。
- `values/global.yaml` 模式读取 `references/values.md`。

只读取实际检测到的模式对应 reference。
