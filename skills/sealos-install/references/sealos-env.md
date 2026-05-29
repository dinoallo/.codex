# 旧版 sealos.env 模式

仅当基础包目录包含 `sealos.env` 时使用此模式。

如果用户尚未提供下载包矩阵，先询问矩阵。默认不要询问 SSH 账号密码；除非用户主动覆盖，否则使用 `sealos/1234`。

## 边界

- 此模式适用于通过 `sealos.env` 和 `SEALOS_V2_*` 变量配置的旧版包。
- 不要把此模式用于只包含 `values/global.yaml` 的包。
- 除非用户明确要求转换，否则不要创建 `values/global.yaml` 迁移。
- 永远不要执行 `sealos reset`。

## 域名检查

安装前，根据用户提供的 IP 推导预期域名：

```bash
SEALOS_V2_CLOUD_DOMAIN="<ip>.nip.io"
```

报告 `sealos.env` 是否已经匹配预期域名。除非用户明确要求在安装前修改配置，否则不要编辑 `sealos.env`。

## 通用检查

- 如果存在 `SEALOS_V2_CLOUD_PORT`，确认其值；默认 HTTPS 端口通常是 `443`。
- 除非任务明确要求修改，否则保留用户已有配置。
- 不要为了检查而在 agent 进程里 source `sealos.env`，应按文本解析或编辑。
- `info` 输出中的 Sealos Cloud 登录用户名和登录密码必须明文输出；下载 URL 签名、token、key、非登录密钥和 URI 内嵌凭据必须脱敏。

## 命令

在基础包目录执行安装入口：

```bash
./sealos-pro.sh install
```

或：

```bash
./sealos-oss.sh install
```

安装后执行匹配的 info 入口：

```bash
./sealos-pro.sh info
```

或：

```bash
./sealos-oss.sh info
```

然后在本地信任浏览器证书，再输出最终报告：

```bash
curl https://objectstorageapi.hzh.sealos.run/paxilf30-static/cert.sh | bash -s -- --mode auto "<cloud-https-url>"
```

从安装后或重跑检查时的 `info` 输出中取 HTTPS URL。如果 `info` 没有可用 URL，则使用 `https://<ip>.nip.io:443`。该命令必须在本地执行，不要在目标主机上执行。证书信任是最终成功报告的强制门禁，不允许因为以前执行过、证书可能已存在、本次只是重新检查或本次只跑增量包而跳过；`cert.sh --mode auto` 必须按幂等动作重新执行。证书信任成功后，再执行一次匹配的 `info` 命令，并把最终输出写入报告。如果证书信任失败，报告 `Certificate trust: FAIL`，不要宣称安装完全成功。

Pro/OSS 类型以下载包矩阵里的基础包行为准。如果选中的脚本不存在，基础包检查失败。增量包后续可以执行 `sealos run <运行目标>`。
