# Namecheap API setup

**English** · [简体中文](setup.zh-CN.md)

Namecheap requires production API access and an IPv4 allowlist. The API returns
XML, which the checker parses for availability.

## 1. Open API Access

Sign in to [Namecheap](https://www.namecheap.com/), then open
**Profile → Tools → Business & Dev Tools → Manage API Access**. You can test
the integration in the sandbox first.

## 2. Enable access and whitelist IPv4

Enable API access, accept the terms, and add the public IPv4 address of the
machine that will run the skill. Add all required values to `.env`:

```dotenv
NAMECHEAP_API_USER=your_api_user
NAMECHEAP_USERNAME=your_username
NAMECHEAP_API_KEY=your_api_key
NAMECHEAP_CLIENT_IP=your_public_ipv4
```

The username and API user are often the same, but keep both variables explicit.

## 3. Verify the setup

Return to `/letsfinddomain-skill` and ask:

```text
Check example.com and show its availability and renewal price.
```

The result should be `taken`.

![Namecheap API documentation](assets/api-access-docs.jpg)
