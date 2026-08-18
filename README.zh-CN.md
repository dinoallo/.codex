# Codex Control Deck

[English](README.md)

```text
 ____   ___ _____    ____ ___  ____  _______  __
|  _ \ / _ \_   _|  / ___/ _ \|  _ \| ____\ \/ /
| | | | | | || |   | |  | | | | | | |  _|  \  /
| |_| | |_| || |   | |__| |_| | |_| | |___ /  \
|____/ \___/ |_|    \____\___/|____/|_____/_/\_\
```

Codex Control Deck 是我的个人 `.codex` dotfiles 仓库：这里放着手工调校过的全局 agent 规则、自定义斜杠命令 prompt，以及本地 skills，用来定义 Codex 在我的机器上怎么工作。仓库只跟踪会定义行为的文件，密钥、日志、会话、缓存和机器本地状态都留在版本控制之外。

## 这里有什么

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | Codex 配置树下 agent 的个人全局工作规则。 |
| `docs/` | 分享这套配置时给人看的说明，包括 skill 目录和安全 auth 配置示例。 |
| `prompts/` | 自定义 prompt 文件，目前主要服务于 OPSX/OpenSpec 变更工作流。 |
| `skills/` | 用户维护的 skills，用于扩展 Git、README 编写、GitHub Actions 和 Proxmox 基础设施等行为。 |
| `scripts/` | 本地维护脚本，用来让 dotfiles 操作可重复。 |
| `.gitignore` | allowlist 风格的忽略规则，用来避免运行时状态和私有配置进入提交。 |

## 终端地图

```text
.
|-- AGENTS.md
|-- README.md
|-- README.zh-CN.md
|-- docs/
|   |-- gh-auth-profiles.example.toml
|   |-- skills.md
|   `-- skills.zh-CN.md
|-- prompts/
|   `-- opsx-*.md
|-- scripts/
|   `-- skill-vendor.py
|-- skills/
|   |-- git-workflow-as-user/
|   |-- infra/
|   |-- third-party.lock.json
|   |-- third-party.toml
|   |-- write-github-actions-workflows/
|   `-- write-readmes/
`-- .gitignore
```

## Skills

Skills 是这套配置的主要扩展点。每个 skill 位于 `skills/<name>/`，用
`SKILL.md` 保存 agent-facing 指令，并可选配 `agents/openai.yaml` 作为 UI
元数据。

查看 [docs/skills.zh-CN.md](docs/skills.zh-CN.md) 了解 skill 目录、维护约定
和推荐的 GitHub auth profile 配置。可提交的脱敏示例
[docs/gh-auth-profiles.example.toml](docs/gh-auth-profiles.example.toml) 展示了如何
把 `gh` CLI 命令路由到由 SOPS 加密的 fine-grained PAT。

不要在单个 skill 目录里添加 README。给人看的总览材料放在 `docs/`；详细的
agent 指令继续放在各 skill 的 `SKILL.md` 或 `references/` 文件中。

## 第三方 Skills

第三方 skills 会 vendor 到 `skills/<name>`，这样不同机器之间只需要普通
`git pull` 就能同步。来源清单放在 `skills/third-party.toml`，实际锁定的
commit 放在 `skills/third-party.lock.json`。

添加或更新第三方 Codex skill 时，使用 `third-party-skill-vendor` skill。
`npx skills add ...` 这类外部安装命令可以用来辅助确认来源，但最终仓库状态
应来自下面的 manifest、lock 文件和可审查的 vendored diff。

添加一个这样的条目：

```toml
[[skill]]
name = "example"
repo = "owner/repo"
path = "skills/.curated/example"
ref = "main"
dest = "skills/example"
```

然后运行：

```bash
python3 scripts/skill-vendor.py update example
python3 scripts/skill-vendor.py verify example
git diff
```

`update` 会跟踪配置的 `ref`，把 skill 复制到 `skills/<name>`，并在 lock 文件
里记录精确 commit。`sync` 会从锁定 commit 重新安装，`verify` 会检查已
vendor 的文件是否仍匹配 lock。脚本默认拒绝覆盖目标目录里的未提交改动，除非
显式传入 `--force`。

## 操作备忘

- 把这个仓库当作更锋利的个人 dotfiles：小改动也可能改变之后的 agent 行为。
- 项目产物默认使用英文；需要时同步添加本地化文档。
- 不要提交 `auth.json`、`config.toml`、会话日志、memories、shell snapshots、缓存或生成的运行时状态。
- prompt 和 skill 优先做小范围定向修改；只有行为契约真的变化时才做大规模重写。
- 第三方 skill 更新应保留为可审查的 vendor diff，并同时更新 lock 文件里的 commit。
- infra skill 的 stack 密钥和生成产物应保留在已忽略的文件中，例如 `tf.vars`、`.terraform/`、`.artifacts/` 和 Terraform state。
- 新增需要长期维护的区域时，先更新 `.gitignore`，确保目标文件可跟踪，同时私有文件仍被忽略。

### 代码仓库 Worktree

处理本地 Git 代码仓库时，Codex 会先在当前启动目录下创建独立的分支
worktree，例如：`./.worktrees/codex-<repo>-<timestamp>-<pid>`。

后续所有代码读取、编辑、测试和构建都在这个 worktree 中进行，不会自动
修改主工作树。主工作树已有的未提交改动会原样保留，也不会自动复制到新
worktree。worktree 不会自动删除，任务结束时会报告其路径和分支。

## 快速检查

```bash
git status --short
git diff --check
git check-ignore -v auth.json config.toml version.json
```

如果这些检查都干净，这块控制台大概率可以起飞。
