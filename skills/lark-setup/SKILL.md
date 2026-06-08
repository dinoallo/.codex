---
name: lark-setup
description: "Use when initializing Lark/Feishu agent support from scratch, installing or checking lark-cli, bootstrapping lark-cli config, syncing vendored lark-* Codex skills under ~/.codex, running lark-cli doctor, or helping a user prepare authentication and scopes before using lark skills. Use for requests like 初始化 lark skill, 安装飞书 skill, 配置 lark-cli, 首次使用飞书工具, or setup Lark skills."
metadata:
  short-description: "Bootstrap lark-cli and Lark skills"
---

# Lark Setup

本技能是 Lark/飞书能力的初始化入口，负责串起 CLI 安装检查、本地 skill
同步、首次配置、健康检查和用户授权准备。它不替代 `lark-doc`、`lark-drive`、
`lark-base`、`lark-calendar` 等业务技能。

## 前置上下文

执行任何 `lark-cli --help` 之外的命令前，必须先读：

- `../lark-shared/SKILL.md`：配置、认证、二维码、身份、权限、更新和高风险确认规则。

在 `~/.codex` 下安装、同步或更新 `lark-*` skills 时，还必须读：

- `../third-party-skill-vendor/SKILL.md`

## 初始化流程

1. 检查环境：
   - 运行 `command -v lark-cli`。
   - 如果已安装，运行 `lark-cli --version`；需要检查更新且允许联网时，运行
     `lark-cli update --check --json`。
   - 如果未安装，不要静默猜测包管理器。告诉用户缺少 `lark-cli`，并按
     `larksuite/cli` 的官方安装方式或用户提供的安装命令执行；受限环境中的联网安装需要用户明确批准。
   - 如果发现可更新版本，先报告。只有用户确认后才执行 `lark-cli update`，
     因为它会修改本机 CLI 安装。
2. 当工作目录是 `~/.codex`，或用户询问 Codex skill 安装时，同步本地 Lark skills：
   - 不要把 `npx skills add ...` 当作本仓库的最终状态。
   - 使用 `skills/third-party.toml`、`skills/third-party.lock.json` 和
     `scripts/skill-vendor.py`。
   - 当前已配置的 Lark skills 用下面命令更新和验证：

```bash
python3 scripts/skill-vendor.py update lark-shared lark-doc lark-drive lark-base lark-task lark-wiki
python3 scripts/skill-vendor.py verify lark-shared lark-doc lark-drive lark-base lark-task lark-wiki
```

3. 按需初始化或绑定 CLI 配置：
   - 创建新配置前，先运行 `lark-cli doctor --offline` 检查本地状态。
   - 如果 `OPENCLAW_HOME`、`HERMES_HOME` 或 `LARK_CHANNEL` 提供了 agent
     凭证，优先考虑 `lark-cli config bind`，不要并行创建新应用。执行 bind
     前必须让用户明确确认意图和身份策略：
     - `bot-only`：更安全的默认选项；不能访问个人用户资源。
     - `user-default`：允许用户身份；访问个人日历、邮箱、云空间等资源时需要。
   - 如果没有可绑定的 agent 来源，运行 `lark-cli config init --new`。
   - 如果命令输出 `verification_url`、`verification_uri_complete` 或
     `console_url`，严格按 `lark-shared` 处理：用 `lark-cli auth qrcode`
     生成二维码，同时展示原样 URL 和二维码，不要改写 URL。
4. 检查健康状态：
   - 运行 `lark-cli doctor --offline` 检查本地配置和认证状态。
   - 需要且允许联网检查时，再运行 `lark-cli doctor`。
   - 根据输出判断还缺配置、网络连通性还是授权。
5. 只为用户明确需要的领域准备授权：
   - 优先使用最小权限 scope 登录，例如：
     `lark-cli auth login --scope "<scope>" --no-wait --json`.
   - 把返回的 URL 和二维码发给用户后，结束本轮并交还控制权。
   - 用户回复授权完成后，再执行：
     `lark-cli auth login --device-code <device_code>`.

## Scope 选择

具体工作需要哪些 scope，由对应业务 skill 判断。如果用户只要求初始化，且没有
指定业务领域，先完成配置和 `doctor` 检查；不要预先申请宽泛 scope。

常见后续分流：

- 文档或云空间文件：切到 `lark-doc` 或 `lark-drive`。
- Base / 多维表格 / bitable：切到 `lark-base`。
- 任务：切到 `lark-task`。
- 知识库：切到 `lark-wiki`。
- 日历、IM、电子表格、邮箱或其他领域：如果已安装对应 `lark-*` skill，就切到它；
  否则在 `~/.codex` 下通过第三方 vendor workflow 添加。

## 汇报

初始化结束时汇报：

- `lark-cli` 状态：缺失、已安装版本或可更新版本。
- Skill 同步状态：更新/验证过的 skill 名称，以及 lock commit 是否变化。
- 配置状态：已初始化、已配置或等待用户操作。
- 认证状态：未请求、等待 device 授权、已完成，或被缺失 scope / 管理员配置阻塞。
- 成功安装或更新 skill 后，提醒用户重启 Codex。
