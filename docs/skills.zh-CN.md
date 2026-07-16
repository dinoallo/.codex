# Skills

[English](skills.md)

这套配置用 skills 作为 Codex 的长期行为层。一个 skill 应该教会 agent 做某类
具体工作，而不是为了自己再维护一份面向用户的说明。

## 目录结构

```text
skills/<name>/
|-- SKILL.md
`-- agents/
    `-- openai.yaml
```

`SKILL.md` 是 agent-facing 的行为契约。`agents/openai.yaml` 提供 UI 元数据。
可选的 `references/`、`scripts/` 和 `assets/` 目录用于承载更大的辅助材料。

不要在单个 skill 目录里添加 README。适合分享给人看的说明放在 `docs/`；单个
skill 的执行指令继续放在 `SKILL.md` 或 `references/` 中。

## Skill 分组

当前维护的主要区域是：

| 区域 | Skills |
| --- | --- |
| Git 工作流 | `git-workflow-as-user`, `git-commit-as-user`, `git-push-as-user`, `git-history-as-user`, `git-tag-as-user`, `git-signing-troubleshooter` |
| GitHub CLI | `gh-auth-profile`, `gh-create-pr`, `gh-edit-pr`, `github-actions-debugger` |
| 文档和仓库写作 | `write-readmes`, `write-github-actions-workflows`, `write-cluster-image` |
| Skill 维护 | `third-party-skill-vendor` |
| 基础设施和运维 | `infra`, `sealos-install`, `codex-token-usage-dashboard` |
| Lark 集成 | 目标机器上存在时使用 `lark-*` skills |

发布 fork 或公开副本之前，先检查 private 或公司专用 skills，移除不应该分享的
内容。

## GitHub Auth Profiles

面向 GitHub 的 skills 不应该依赖单一全局 `gh` 账号。有些仓库需要不同用户、
组织审批、SSO 授权或 fine-grained PAT scope。使用 `gh-auth-profile` 将每个
仓库路由到私有 token provider。

私有 profile 配置放在仓库外：

```text
$HOME/.codex/private/gh-auth-profiles.toml
```

使用 [gh-auth-profiles.example.toml](gh-auth-profiles.example.toml) 作为脱敏模板。
不要提交真实 profile 文件、加密 secret 文件、age identity 或明文 token。

开发服务器上推荐用 SOPS + age 保存 token：

```bash
mkdir -p "$HOME/.codex/private" "$HOME/.config/sops/age"
chmod 700 "$HOME/.codex/private" "$HOME/.config/sops/age"
age-keygen -o "$HOME/.config/sops/age/keys.txt"
chmod 600 "$HOME/.config/sops/age/keys.txt"
age-keygen -y "$HOME/.config/sops/age/keys.txt"
SOPS_AGE_RECIPIENTS="age1..." sops "$HOME/.codex/private/github-work-fgpat.sops.yaml"
```

在 SOPS 编辑器里，保存前使用这个明文结构：

```yaml
token: github_pat_xxx
```

保存后，磁盘上的文件应该已经由 SOPS 加密。profile 命令只提取 token 字段：

```toml
[profiles.work]
host = "github.com"
token_command = "sops decrypt --extract '[\"token\"]' \"$HOME/.codex/private/github-work-fgpat.sops.yaml\""

[rules]
"github.com/your-org/*" = "work"
```

GitHub 相关 skills 会把这个命令注入单个 `gh` 进程的 `GH_TOKEN` 或
`GH_ENTERPRISE_TOKEN`。它们不应该运行 `gh auth switch`、`gh auth token`，也不
应该把 token 存进这个仓库。

## 维护检查

修改 skills 或这些说明后，运行最小相关检查：

```bash
python3 skills/.system/skill-creator/scripts/quick_validate.py skills/<name>
git diff --check
git status --short
```
