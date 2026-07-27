# Name.com API setup

**English** · [简体中文](setup.zh-CN.md)

Name.com Core API supports up to 50 domain names in one availability request.

## 1. Open API token settings

Sign in to [Name.com](https://www.name.com/), then open
[Account Settings → API Tokens](https://www.name.com/account/settings/api).

## 2. Create a production token

Create an API token for the production account. Keep the username and token
together and add them to `.env`:

```dotenv
NAMECOM_USERNAME=your_username
NAMECOM_API_TOKEN=your_api_token
```

Use the sandbox credentials only when you intentionally want sandbox results.

## 3. Verify the setup

Return to `/letsfinddomain-skill` and ask:

```text
Check example.com and show its availability and renewal price.
```

`example.com` should be reported as `taken`.

![Name.com API token documentation](assets/api-token-docs.jpg)
