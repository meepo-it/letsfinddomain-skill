# letsfinddomain-skill

**English** · [简体中文](README.zh-CN.md)

> **Find the right name for your next great project.**

letsfinddomain-skill helps you turn an idea into a shortlist of real domain
names. Ask it through your AI tool's slash command and it will:

- generate names around your product, audience, and style;
- check domain availability in bulk;
- show first-year and renewal prices; and
- flag possible brand collisions before you commit to a name.

It is read-only: it never buys domains, transfers domains, or changes DNS.

## Start here

### 1. Install once

If Node.js/npm is available, run:

```bash
npx skills add https://github.com/meepo-it/letsfinddomain-skill \
  --skill letsfinddomain-skill --agent '*' --global --yes
```

### 2. Open the skill

In your AI tool, use:

```text
/letsfinddomain-skill
```

### 3. Ask naturally

Try:

- `Give me 20 .com names for an image compression tool. Check availability and renewal prices.`
- `Find 10 short .com names related to goods.`
- `Check snapkit.com, snapkit.ai, and snapkit.dev.`

You do not need to know Python or construct script arguments. Just describe the
name you want.

## Everyday use cases

Here are a few prompts you can copy and adapt:

- **Naming a new product:** `I am building a lightweight CRM for freelancers. Give me 20 short .com names with a professional feel.`
- **Finding a global version of a local brand:** `My Chinese product is called 智选. Suggest easy-to-pronounce English names and check .com and .ai.`
- **Checking a shortlist:** `Check these 8 names across .com, .io, and .app. Show only confirmed available domains and renewal prices.`
- **Working within a budget:** `Find 15 .com names for a meal-planning app. Keep first-year pricing under $20 and show renewal pricing.`
- **Exploring a product direction:** `Give me 30 names for an AI meeting-notes tool. Avoid names that sound like established products.`
- **Choosing between finalists:** `Compare these three names for memorability, brand collision risk, and domain availability: ...`

## Connect a registrar API

For reliable registrar results and batch checks, configure Spaceship first. It
is the default availability provider whenever its two variables are present.
The skill uses Porkbun's public TLD list for reference prices by default because
Spaceship does not expose ordinary-domain prices through its availability API.
Your account tier and the provider's rules determine the exact permissions and
rate limits.

Start with [Spaceship setup](docs/providers/spaceship/setup.md), or choose a
registrar you already use below. Each guide has the official URL, the exact
page path, numbered steps, required variables, and screenshots.

| Provider | Batch / tool concurrency default | Setup guide |
|---|---|---|
| **Spaceship (default)** | 20/request · 1 in flight · 25 requests/30s | [English](docs/providers/spaceship/setup.md) · [中文](docs/providers/spaceship/setup.zh-CN.md) |
| NameSilo | 20/request · 1 in flight · 20 requests/60s | [English](docs/providers/namesilo/setup.md) · [中文](docs/providers/namesilo/setup.zh-CN.md) |
| GoDaddy | 50/request · 1 in flight · server headers honored | [English](docs/providers/godaddy/setup.md) · [中文](docs/providers/godaddy/setup.zh-CN.md) |
| Name.com | 50/request · 1 in flight · 20 requests/60s | [English](docs/providers/namecom/setup.md) · [中文](docs/providers/namecom/setup.zh-CN.md) |
| Namecheap | 50/request · 1 in flight · 45 requests/60s | [English](docs/providers/namecheap/setup.md) · [中文](docs/providers/namecheap/setup.zh-CN.md) |
| Dynadot | 1 domain/request · 1 in flight · 55 requests/60s | [English](docs/providers/dynadot/setup.md) · [中文](docs/providers/dynadot/setup.zh-CN.md) |
| Porkbun | 1 domain/request · 1 in flight · 60 requests/60s | [English](docs/providers/porkbun/setup.md) · [中文](docs/providers/porkbun/setup.zh-CN.md) |
| Cloudflare Registrar | 20/request · 1 in flight · 180 requests/60s | [English](docs/providers/cloudflare/setup.md) · [中文](docs/providers/cloudflare/setup.zh-CN.md) |

These are the skill's conservative client defaults, not promises about each
provider's quota. The skill batches requests, keeps one request in flight per
provider, and honors provider response headers when available. See the full
[rate-limit notes](references/rate-limits.md).

All provider variables remain in [`.env.example`](.env.example) and the
complete configuration reference is in
[`references/environment.md`](references/environment.md).

If you do not want to connect an account yet, RDAP can provide a limited
keyless trial. It checks registration records rather than registrar purchase
eligibility, and it does not provide premium or renewal pricing. For regular
use, a registrar API is the better path.

## Keep in mind

- A low first-year price can hide a much higher renewal price.
- An available domain can still collide with an existing brand.
- Large candidate lists are grouped into batches and paced according to each
  provider's rules.

## License

MIT. The code and original documentation are licensed under MIT. Provider names,
trademarks, screenshots, and external documentation remain the property of
their respective owners.
