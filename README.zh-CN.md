# domain-finder-skill

[English](README.md) · **简体中文**

找到真正注册得下来的域名。批量生成候选、批量查可用性，并且告诉你**续费价**——而不只是首年促销价。

支持 Claude Code、Codex、Cursor、Copilot、Gemini CLI、Aider、Windsurf、Zed，也可以直接在终端里用。

```console
$ python3 scripts/check-domains.py --tlds com,ai,io,dev,xyz zqxjkbwrm
  checking 5 domain(s) via spaceship in 1 request(s)…
| Domain          | Status    | Reg. (1st yr) | Renewal | Note                        |
|-----------------|-----------|---------------|---------|-----------------------------|
| zqxjkbwrm.com   | available | $11.08        | $11.08  |                             |
| zqxjkbwrm.ai    | available | $82.70        | $82.70  |                             |
| zqxjkbwrm.io    | available | $28.12        | $51.80  | renewal 1.8x the first year |
| zqxjkbwrm.dev   | available | $8.75         | $12.87  |                             |
| zqxjkbwrm.xyz   | available | $2.04         | $12.98  | renewal 6.4x the first year |
```

最后一列才是重点。`.xyz` 看起来是 2 美元的域名，其实是 13 美元的域名。

## 目录

- [快速开始](#快速开始)
- [接入你的 AI 工具](#接入你的-ai-工具)
- [常用操作](#常用操作)
- [命令参数](#命令参数)
- [数据来源](#数据来源)
- [设计说明](#设计说明)
- [文档](#文档)
- [边界与限制](#边界与限制)
- [参与贡献](#参与贡献)

## 快速开始

需要 Python 3.8+，零第三方依赖。

**1. 克隆**

```bash
git clone https://github.com/meepo-it/domain-finder-skill.git
cd domain-finder-skill
cp .env.example .env
```

**2. 配一个 key**

去 [Spaceship](https://www.spaceship.com/) 注册（免费，无最低余额要求，不需要 IP 白名单），在 [API Manager](https://www.spaceship.com/application/api-manager/) 创建密钥，两个值都填进 `.env`：

```bash
SPACESHIP_API_KEY=你的_key
SPACESHIP_API_SECRET=你的_secret
```

**3. 验证**

```bash
python3 scripts/check-domains.py example.com     # → taken
```

这样就能用了。

<details>
<summary>不想注册任何账号？</summary>

在 `.env` 里设 `DOMAIN_FINDER_ALLOW_RDAP=1`，会启用一个直接查注册局数据的免密钥方案。

它答不了 `.io` 和 `.co`（这两个注册局不提供 RDAP 服务器），而且一个域名一个请求、比较慢。适合先试用。[详细说明](references/providers.md#rdap-no-credentials)

</details>

其他 provider（NameSilo、Dynadot）和全部配置项见 [`references/environment.md`](references/environment.md)。

## 接入你的 AI 工具

先把仓库克隆到项目能访问到的位置，下面的示例都假设路径是 `tools/domain-finder-skill/`。

### Claude Code

软链到 skills 目录即可。它是按需加载的，不用到就不占上下文：

```bash
ln -s "$PWD/tools/domain-finder-skill" ~/.claude/skills/domain-finder
```

之后直接让它帮你想域名就行。入口是 [`SKILL.md`](SKILL.md)。

### Codex、Gemini CLI、Aider、Windsurf、Zed

这几家读的是跨工具标准 [`AGENTS.md`](AGENTS.md)。把指引片段追加到你项目的 `AGENTS.md`：

```bash
cat tools/domain-finder-skill/install/agents-snippet.md >> AGENTS.md
```

追加完即可用，不需要再改。想全局生效而不是逐项目配置，就追加到 `~/.codex/AGENTS.md`。

### Cursor

直接复制现成的 rule 文件。它用的是 `alwaysApply: false` + description，Cursor 只在对话跟命名相关时才会拉进来，平时不占上下文：

```bash
mkdir -p .cursor/rules
cp tools/domain-finder-skill/install/domain-finder.mdc .cursor/rules/
```

Cursor 现在也读 `AGENTS.md`，所以上面那个片段同样有效。用 rule 文件的好处是能更精细地控制触发时机。

### GitHub Copilot

```bash
mkdir -p .github
cat tools/domain-finder-skill/install/agents-snippet.md >> .github/copilot-instructions.md
```

### 其他工具

脚本就是普通的命令行工具。把 [`AGENTS.md`](AGENTS.md) 指给你的 agent，需要的信息都在里面。

## 常用操作

**查指定域名**

```bash
python3 scripts/check-domains.py acme.com acme.io acme.dev
```

**裸名 × 多个后缀**

```bash
python3 scripts/check-domains.py --tlds com,ai,io snapkit vaultly forgehub
```

**只看注册得下来的，并控制预算**

```bash
python3 scripts/check-domains.py --tlds com snapkit vaultly \
  --available-only --max-price 20
```

**生成候选，再直接查**

```bash
python3 scripts/gen-names.py --roots snap,clip,vault,pix --suffixes ify,ly,kit \
  --max-len 6 | python3 scripts/check-domains.py --tlds com --available-only
```

```console
$ python3 scripts/gen-names.py --roots mock,clip,blur --prefixes up,re,un \
    --patterns prefix+root --max-len 8
upmock  upclip  upblur
remock  reclip  reblur
unmock  unclip  unblur
```

组合模式：`root+suffix` · `prefix+root` · `prefix+root+suffix` · `root+root` · `blend`（两个词根按共同字母融合，`design` + `ignite` → `designite`）。

**大批量之前先看成本**

```bash
python3 scripts/check-domains.py --plan --tlds com,ai,io,dev $(cat names.txt)
```

```console
provider:        spaceship
domains:         50 (0 cached, 50 to query)
requests:        3
budget:          25 requests / 30s
estimated time:  1s
```

更多"约束 → 命令"对照（只要 `.com`、不超过 6 位、`-ify` 结尾、低于 $20 等）见 [`references/query-recipes.md`](references/query-recipes.md)。

## 命令参数

### `check-domains.py`

| 参数 | 作用 |
|---|---|
| `--tlds com,ai,io` | 裸名要拼接的后缀，默认 `com` |
| `--available-only` | 只输出可注册的 |
| `--max-price N` | 隐藏首年价高于此值（美元）的可用域名 |
| `--no-price` | 跳过价格查询 |
| `--no-cache` | 忽略缓存，强制重查 |
| `--plan` | 只显示请求数和耗时预估，不实际发请求 |
| `--json` | JSON 输出 |
| `--quiet` | 不打印进度信息 |

状态列怎么读：

| 值 | 含义 |
|---|---|
| `available` | 无注册记录，可以注册 |
| `taken` | 已注册 |
| `no RDAP for this TLD` | 免密钥方案答不了这个后缀。**这不等于"不可用"** |
| `lookup failed` | 重试后仍失败。**未被确认可用** |
| `unknown` | provider 返回了预期外的内容 |

退出码：`0` 全部查明 · `1` 无有效输入 · `2` 未配置任何 provider · `3` 部分失败，这些域名**未被确认可用**。

### `gen-names.py`

| 参数 | 作用 |
|---|---|
| `--roots snap,clip` | 词根（必填） |
| `--prefixes up,re` | 前缀 |
| `--suffixes ify,ly` | 后缀 |
| `--patterns root+suffix,blend` | 要生成哪些组合 |
| `--min-len N` / `--max-len N` | 长度过滤 |
| `--no-filter` | 跳过可读性过滤 |

## 数据来源

| 用途 | 来源 | 凭据 |
|---|---|---|
| 可用性 | Spaceship，20 个域名/请求 | 免费账号 |
| — 备选 | NameSilo | 免费账号 |
| — 回退 | RDAP（走 `rdap.org`） | **不需要** |
| 价格 | Porkbun 公开 TLD 价目表，907 个后缀 | **不需要** |
| — 可选 | Dynadot，逐个域名的精确报价 | 免费账号 |

价格之所以能零配置开箱即用，是因为 Porkbun 把整份价目表放在一个**完全不需要鉴权**的接口上。

一共调研了 11 家，能实测的都实测了——各自要什么、实际返回什么、哪些有坑：[`references/providers.md`](references/providers.md)。

## 设计说明

这三件事是同类工具通常没做对的。

<details>
<summary><b>显示续费价，而不只是促销价</b></summary>

`.xyz` 首年 $2.04、之后每年 $12.98，涨 6.4 倍；`.io` 差不多翻倍。只显示首年价是在误导人，所以两列一直都在，涨幅超过 1.5 倍会在 `Note` 列标出来。

</details>

<details>
<summary><b>让免费查询工具说谎的那个 RDAP 陷阱</b></summary>

基于 RDAP 的查询工具经常会报 `github.io` **可用**。原因是：

| 域名 | 实际 | rdap.org 返回 |
|---|---|---|
| `openai.com` | 已注册 | 200 ✅ |
| `vercel.app` | 已注册 | 200 ✅ |
| **`github.io`** | **已注册** | **404 ← 会被读成"可用"** |
| **`google.co`** | **已注册** | **404 ← 会被读成"可用"** |

没有 RDAP 服务器的后缀返回的也是 404，跟"没有注册记录"完全一样。`.io` 和 `.co` 就都不提供。

这个仓库会先拉 IANA bootstrap 名单（1200 个支持 RDAP 的后缀）缓存一周，不在名单里就报 `no RDAP for this TLD`，而不是瞎猜。

</details>

<details>
<summary><b>进程退出后依然有效的限速</b></summary>

AI agent 一轮里会反复调这个脚本——生成、查、调整、再查——有时还会并行跑好几个 agent。**每次调用都是独立进程**，所以进程内的 sleep 对彼此毫无保护作用。

实际做法：

- **请求预算落盘。** 上一次运行花掉的额度，对下一次运行仍然算数。
- **`flock` 加锁守护状态**，并行进程排队，而不是各自读到"已用 0 次"然后一起发。
- **一个 429 让所有进程一起停**，通过共享冷却时间戳；遵循 `Retry-After`，否则指数退避 + 随机抖动。
- **结果缓存 1 小时。** 50 个域名的重复查询从 26.8s 降到 0.16s，请求数从 3 降到 0。
- **失败绝不吞掉。** 查询失败的域名会单独列出，并被 `--available-only` 排除。

实测数据、设计理由和调参开关见 [`references/rate-limits.md`](references/rate-limits.md)。

</details>

## 文档

| 文件 | 内容 |
|---|---|
| [`SKILL.md`](SKILL.md) | Claude Code 入口 |
| [`AGENTS.md`](AGENTS.md) | 跨工具入口（Codex、Cursor、Copilot 等） |
| [`references/environment.md`](references/environment.md) | 所有环境变量，每个凭据从哪来 |
| [`references/providers.md`](references/providers.md) | 服务商 API 调研，实测行为与陷阱 |
| [`references/rate-limits.md`](references/rate-limits.md) | 各家限速、缓存、如何调参 |
| [`references/query-recipes.md`](references/query-recipes.md) | 常见约束 → 具体命令 |
| [`references/naming-guide.md`](references/naming-guide.md) | 词根、词缀、组合模式 |

> 参考文档正文为英文，方便外部贡献者阅读和提 PR。

## 边界与限制

**只读。** 这个工具只查可用性和价格，不购买、不转移、不改 DNS。购买请在你自己的注册商账号下完成。

**可用性是一次查询，不是承诺。** 注册局保留词、溢价定价、商标争议，这些任何 API 都不会告诉你。真正付款前请用 `--no-cache` 再查一次。

**对你的名字没有意见。** 没有长度规则、没有价格上限、没有后缀排序。`references/naming-guide.md` 是调色板，不是白名单。

## 参与贡献

新增一个 provider 只需要写一个函数加一条字典项，见 [Adding a provider](references/providers.md#adding-a-provider)。其中有两条比代码更重要：

- **绝不要把语义不明的响应映射成 `available`**，请用 `unknown`。误报"已注册"只是让人错过一个好名字；误报"可用"会浪费别人的购买尝试，并且毁掉对工具的信任。
- **把没查明的如实报出来。** 沉默会被读成"一切正常"。

特别欢迎对服务商调研表的勘误——注册商的 API 政策一直在变，表里的准入门槛是最容易过期的部分。

## 许可

MIT
