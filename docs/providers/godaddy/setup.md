# GoDaddy API setup

**English** · [简体中文](setup.zh-CN.md)

The checker uses GoDaddy's read-only domain availability API and its bulk
availability endpoint.

## 1. Open the developer portal

Sign in to the [GoDaddy Developer Portal](https://developer.godaddy.com/), then
open [How to Authenticate](https://developer.godaddy.com/en/docs/api-users/auth/how-to).

## 2. Create a Personal Access Token

Create a PAT with the `domains.domain:read` scope. Copy it immediately and put
it in `.env`:

```dotenv
GODADDY_PAT=your_personal_access_token
```

Only use a read scope for this skill. It never registers or changes domains.

## 3. Verify the setup

Return to `/letsfinddomain-skill` and ask:

```text
Check example.com and show its availability and renewal price.
```

The result should be `taken`. GoDaddy's rate-limit response headers are handled
by the checker automatically.

![GoDaddy Personal Access Token documentation](assets/pat-docs.jpg)
