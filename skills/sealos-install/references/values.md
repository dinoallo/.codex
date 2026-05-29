# values/global.yaml 模式

仅当基础包目录不包含 `sealos.env` 且包含 `values/global.yaml` 时使用此模式。

如果用户尚未提供下载包矩阵，先询问矩阵。默认不要询问 SSH 账号密码；除非用户主动覆盖，否则使用 `sealos/1234`。

## 边界

- 此模式适用于通过 `values/global.yaml` 配置的新版包。
- 不要读取、创建、修改或依赖 `sealos.env`。
- 不要在 values 模式包中使用 `SEALOS_V2_*` 变量。
- 将本地包文件 `values/global.yaml` 视为用户配置来源。
- 永远不要执行 `sealos reset`。

## 域名检查

安装前，根据用户提供的 IP 推导预期域名：

```yaml
global:
  http:
    domain: <ip>.nip.io
```

报告 `values/global.yaml` 是否已经匹配预期域名。除非用户明确要求在安装前修改配置，否则不要编辑 YAML。

## 通用检查

- 确认 `global.http.httpsPort`；默认通常是 `443`。
- Pro 包可能包含 `global.objectStorage` 和高级 OpenEBS 配置。
- OSS 包 schema 更小；除非包 schema 已经包含对应字段，否则不要给 OSS 添加 Pro 专属字段。
- 除非任务明确要求修改，否则保留用户已有配置。
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
