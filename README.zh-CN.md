# letsfinddomain-skill

[English](README.md) · **简体中文**

> **为你的下一个伟大项目，找到正确的名字。**

letsfinddomain-skill 帮你把一个想法变成一组真实可用的域名候选。通过 AI 工具的 slash 命令直接描述需求，它会：

- 根据你的产品、用户和风格生成名字；
- 批量查询域名可用性；
- 同时展示首年价格和续费价格；
- 在你决定之前提醒可能的品牌冲突。

它只做查询：不会购买域名、转移域名，也不会修改 DNS。

## 开始使用

### 1. 安装一次

如果已经安装 Node.js/npm，运行：

```bash
npx skills add https://github.com/meepo-it/letsfinddomain-skill \
  --skill letsfinddomain-skill --agent '*' --global --yes
```

这条命令会把 skill 全局安装到支持的工具中，包括 Claude Code、Codex 和 Cursor，不需要为每个工具重复安装。安装或更新后，重新打开对应工具或会话，再输入 `/letsfinddomain-skill` 即可。

如果只想安装到某一个工具，可以把 `--agent '*'` 换成 `--agent claude-code`、`--agent codex` 或 `--agent cursor`。

### 更新

发布新版本后，手动执行：

```bash
npx skills update letsfinddomain-skill --global --yes
```

Skill 运行过程中不会静默自动更新。这样可以让代码和权限变化都经过用户明确确认。如果 AI 工具已经加载了旧版本，更新后重新打开会话即可。

### 2. 打开 skill

在 AI 工具中输入：

```text
/letsfinddomain-skill
```

### 3. 直接描述需求

例如：

- `帮我为一个图片压缩工具想 20 个 .com 域名，并查可用性和续费价。`
- `帮我找 10 个 goods 相关的短 .com 域名。`
- `检查 snapkit.com、snapkit.ai 和 snapkit.dev。`

你不需要会 Python，也不需要自己拼接脚本参数，只要说清楚想要什么名字即可。

## 日常使用案例

下面这些例子可以直接复制，再按你的项目修改：

- **给新产品起名：** `我正在做一个面向自由职业者的轻量 CRM，帮我想 20 个简短、有专业感的 .com 域名。`
- **把中文品牌做成国际品牌：** `我的中文产品叫“智选”，帮我想一些容易读、容易记的英文名，并查询 .com 和 .ai。`
- **检查候选名单：** `帮我检查这 8 个名字在 .com、.io、.app 上的情况，只显示确认可用的域名和续费价。`
- **按预算筛选：** `帮我为一个饮食计划 App 找 15 个 .com 域名，首年价格控制在 20 美元以内，同时显示续费价。`
- **探索产品方向：** `帮我为一个 AI 会议纪要工具想 30 个名字，避免听起来像已有知名产品。`
- **在几个候选中做决定：** `帮我比较这三个名字的记忆点、品牌冲突风险和域名可用性：……`

## 连接域名注册商 API

如果想获得可靠的注册商查询结果和批量查询，建议优先配置 Spaceship。只要填写它的两个配置项，skill 就会默认优先使用 Spaceship 查询可用性。由于 Spaceship 的可用性接口不提供普通域名价格，价格默认使用 Porkbun 的公开 TLD 价格表作为参考。具体权限和速率取决于你的账号等级及平台规则。

建议把 Provider 凭据设置为系统环境变量，这样安装后的 slash skill 在任何目录都能使用。请按照[macOS、Linux 或 Windows 配置步骤](references/environment.md#system-environment-variables)操作。本地仓库仍然支持使用 `.env` 文件。

可以从推荐的 [Spaceship 配置说明](docs/providers/spaceship/setup.zh-CN.md) 开始，也可以选择你正在使用的注册商。每份说明都包含官方地址、准确页面路径、1/2/3 步骤、所需配置项和截图。

| 平台 | 批量 / skill 默认并发策略 | 配置说明 |
|---|---|---|
| **Spaceship（默认）** | 每次 20 个域名 · 同时 1 个请求 · 25 次/30 秒 | [中文](docs/providers/spaceship/setup.zh-CN.md) · [English](docs/providers/spaceship/setup.md) |
| NameSilo | 每次 20 个域名 · 同时 1 个请求 · 20 次/60 秒 | [中文](docs/providers/namesilo/setup.zh-CN.md) · [English](docs/providers/namesilo/setup.md) |
| GoDaddy | 每次 50 个域名 · 同时 1 个请求 · 遵循服务端响应头 | [中文](docs/providers/godaddy/setup.zh-CN.md) · [English](docs/providers/godaddy/setup.md) |
| Name.com | 每次 50 个域名 · 同时 1 个请求 · 20 次/60 秒 | [中文](docs/providers/namecom/setup.zh-CN.md) · [English](docs/providers/namecom/setup.md) |
| Namecheap | 每次 50 个域名 · 同时 1 个请求 · 45 次/60 秒 | [中文](docs/providers/namecheap/setup.zh-CN.md) · [English](docs/providers/namecheap/setup.md) |
| Dynadot | 每次 1 个域名 · 同时 1 个请求 · 55 次/60 秒 | [中文](docs/providers/dynadot/setup.zh-CN.md) · [English](docs/providers/dynadot/setup.md) |
| Porkbun | 每次 1 个域名 · 同时 1 个请求 · 60 次/60 秒 | [中文](docs/providers/porkbun/setup.zh-CN.md) · [English](docs/providers/porkbun/setup.md) |
| Cloudflare Registrar | 每次 20 个域名 · 同时 1 个请求 · 180 次/60 秒 | [中文](docs/providers/cloudflare/setup.zh-CN.md) · [English](docs/providers/cloudflare/setup.md) |

以上是 skill 的保守客户端默认值，不代表平台承诺的固定配额。skill 会自动批量、限速，并在平台返回响应头时遵循平台的实时规则。完整说明见[限速文档](references/rate-limits.md)。

全部 Provider 配置项仍保留在 [`.env.example`](.env.example)，完整配置说明见 [`references/environment.md`](references/environment.md)。

如果暂时不想连接账号，也可以使用 RDAP 做有限试用。但它查的是注册记录，不是注册商是否愿意卖给你，也不会提供 premium 或续费价格。正式使用建议连接注册商 API。

## 选名字时记住三件事

- 首年价格低，不代表续费价格也低。
- 域名可用，不代表这个名字没有品牌冲突。
- 大批候选会按各平台规则自动分批、限速查询。

## 许可

MIT。代码和原创文档采用 MIT License；平台名称、商标、截图和外部文档归各自权利人所有。
