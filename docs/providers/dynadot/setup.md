# Dynadot API setup

**English** · [简体中文](setup.zh-CN.md)

Dynadot's default Regular account policy is one thread and about one request
per second. The checker uses that conservative pace by default.

## 1. Open API settings

Sign up or sign in to [Dynadot](https://www.dynadot.com/?7F7B7B8j9N9A8a7z), then open
**Account Control Panel → Tools → API**.

## 2. Create or copy the API key

Enable API access and create or copy the API key. Add it to `.env`:

```dotenv
DYNADOT_API_KEY=your_api_key
```

If your account is Bulk or Super Bulk, review the documented tier limits before
raising the local `DOMAIN_FINDER_DYNADOT_LIMIT` value.

## 3. Verify the setup

Return to `/letsfinddomain-skill` and ask:

```text
Check example.com and show its availability and renewal price.
```

For exact Dynadot registration and renewal quotes, optionally set:

```dotenv
DOMAIN_FINDER_PRICE_SOURCE=dynadot
```

![Dynadot API documentation](assets/api.jpg)
