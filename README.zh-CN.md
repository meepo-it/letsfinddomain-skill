# domain-finder-skill

[English](README.md) · **简体中文**

一个 Claude Code skill，用来找到真正注册得下来的域名：批量生成候选、批量查可用性，并且在你掏钱之前同时告诉你**首年价和续费价**。

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

最后一列才是重点。`.xyz` 看起来是 2 美元的域名，实际上是 13 美元的域名。

## 为什么要有这个

市面上的域名查询工具，通常至少踩中下面一条：

- **只给你看促销价。** `.xyz` 首年 $2.04、续费 $12.98，涨 6.4 倍。这里两列都显示，涨幅超过 1.5 倍会主动标出来。
- **可用性会误报。** 基于 RDAP 的工具会告诉你 `github.io` 可以注册——因为 `.io` 根本没有 RDAP 服务器，而"没有服务器"和"没有注册记录"返回的都是 404，不先查就分不出来。这个工具会先查，分不出来时报 *unsupported*，而不是瞎猜。
- **不管限速。** AI agent 一轮对话里会反复调脚本，还可能并行调。进程内 sleep 对跨进程的调用毫无保护作用。这里的请求预算是**带锁落盘**的。
- **对你的名字有意见。** 这里没有长度规则、没有价格上限、没有后缀排序——那些是你自己的事。

## 环境要求

Python 3.8+。零第三方依赖，只用标准库。

## 安装

```bash
git clone https://github.com/meepo-it/domain-finder-skill.git
cd domain-finder-skill
cp .env.example .env
```

在 `.env` 里填上 Spaceship 的 key 和 secret——免费账号即可，无最低余额要求，不需要 IP 白名单：

```bash
SPACESHIP_API_KEY=你的_key
SPACESHIP_API_SECRET=你的_secret
```

验证：

```bash
python3 scripts/check-domains.py example.com   # 应该显示 taken
```

暂时不想注册账号？设 `DOMAIN_FINDER_ALLOW_RDAP=1` 可以启用免密钥回退——但请先读[那个坑](references/providers.md#rdap-no-credentials)，它答不了 `.io` 和 `.co`。

其他方案和完整说明见 [`references/environment.md`](references/environment.md)。

### 作为 Claude Code skill 使用

```bash
ln -s "$(pwd)" ~/.claude/skills/domain-finder
```

之后直接让 Claude 帮你想域名，它会自动用上这个 skill。入口是 `SKILL.md`。

## 用法

```bash
# 查指定域名
python3 scripts/check-domains.py acme.com acme.io

# 裸名 × 多个后缀
python3 scripts/check-domains.py --tlds com,ai,io snapkit vaultly forgehub

# 只看注册得下来的，且控制预算
python3 scripts/check-domains.py --tlds com snapkit vaultly \
  --available-only --max-price 20

# 大批量之前先预估请求数和耗时
python3 scripts/check-domains.py --plan --tlds com,ai,io,dev $(cat names.txt)

# 机器可读输出
python3 scripts/check-domains.py --json acme.com
```

### 生成候选名

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

支持的组合模式：`root+suffix`、`prefix+root`、`prefix+root+suffix`、`root+root`、`blend`（两个词根按共同字母融合，`design` + `ignite` → `designite`）。

更多"约束 → 命令"的对照——只要 `.com`、不超过 6 个字符、要 `-ify` 结尾、单价低于 $20 等——见 [`references/query-recipes.md`](references/query-recipes.md)。

## 参数

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

退出码：`0` 全部查明 · `1` 无有效输入 · `2` 未配置任何 provider · `3` 部分失败，这些域名**未被确认可用**。

## 数据来源

| 用途 | 来源 | 凭据 |
|---|---|---|
| 可用性 | Spaceship（20 个域名/请求） | 免费账号 |
| — 备选 | NameSilo | 免费账号 |
| — 回退 | RDAP（走 `rdap.org`） | **不需要** |
| 价格 | Porkbun 公开 TLD 价目表，907 个后缀 | **不需要** |
| — 可选 | Dynadot，逐个域名的精确报价 | 免费账号 |

数据源是可插拔的，而且价格开箱即用——因为 Porkbun 把整份价目表放在一个**完全不需要鉴权**的接口上。

一共调研了 11 家：各自要什么、实际返回什么、哪些有坑，都写在 [`references/providers.md`](references/providers.md)。

## 限速处理

这是多数工具略过的部分。要点：

- **预算落盘持久化**，所以上一次运行花掉的额度，对下一次运行仍然算数。
- **用 `flock` 守护状态文件**，并行的多个 agent 会排队，而不是各自读到"已用 0 次"然后一起发请求。
- **一个 429 会让所有进程一起停**，通过共享的冷却时间戳；遵循 `Retry-After`，否则指数退避 + 随机抖动。
- **结果缓存 1 小时**，反复查重叠的候选集不花任何请求。实测 50 个域名的重复查询：26.8s → 0.16s，3 个请求 → 0 个。
- **失败会如实上报，绝不吞掉。** 查询失败的域名不等于"可用"。

设计理由、实测数据和调参开关见 [`references/rate-limits.md`](references/rate-limits.md)。

## 文档

| 文件 | 内容 |
|---|---|
| [`SKILL.md`](SKILL.md) | skill 入口，Claude 遵循的工作流 |
| [`references/environment.md`](references/environment.md) | 所有环境变量，每个凭据从哪来 |
| [`references/providers.md`](references/providers.md) | 服务商 API 调研，实测行为与陷阱 |
| [`references/rate-limits.md`](references/rate-limits.md) | 各家限速、工具的应对、如何调参 |
| [`references/query-recipes.md`](references/query-recipes.md) | 常见约束 → 具体命令 |
| [`references/naming-guide.md`](references/naming-guide.md) | 词根、词缀、组合模式 |

> 参考文档正文为英文，方便外部贡献者阅读和提 PR。

## 边界

只读。这个工具只查可用性和价格，**不购买、不转移、不改 DNS**。购买请在你自己的注册商账号下完成。

另外，可用性是一次查询，不是承诺。注册局保留词、溢价定价、商标争议，这些任何 API 都不会告诉你。真正付款前，请用 `--no-cache` 再查一次。

## 参与贡献

新增一个 provider 只需要写一个函数加一条字典项，见 [Adding a provider](references/providers.md#adding-a-provider)。其中有两条比代码更重要：

- **绝不要把语义不明的响应映射成 `available`**，请用 `unknown`。误报"已注册"只是让人错过一个好名字；误报"可用"会浪费别人的购买尝试，并且毁掉对工具的信任。
- **把没查明的如实报出来。** 沉默会被读成"一切正常"。

特别欢迎对服务商调研表的勘误——注册商的 API 政策一直在变，表里的准入门槛是最容易过期的部分。

## 许可

MIT
