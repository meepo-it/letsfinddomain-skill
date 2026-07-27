# NameSilo API setup

**English** · [简体中文](setup.zh-CN.md)

NameSilo supports batch availability checks. Automated batch traffic must use
the `/apibatch` endpoint; the checker already does this for you.

## 1. Open API Manager

Sign up or sign in to [NameSilo](https://www.namesilo.com/?rid=2f35224vs), then open
[Account → API Manager](https://www.namesilo.com/account/api-manager).

## 2. Generate an API key

Generate a key and optionally configure IP restrictions. NameSilo displays a
new key only after generation, so store it safely. Set it as a system
environment variable (recommended); see the
[cross-platform setup](../../../references/environment.md#system-environment-variables):

```dotenv
NAMESILO_API_KEY=your_key
```

Do not put the key in a command, README, screenshot, or Git commit.

## 3. Verify the setup

Return to `/letsfinddomain-skill` and ask:

```text
Check example.com and show its availability and renewal price.
```

The checker should return `taken` for `example.com`.

![NameSilo API Manager](assets/api-manager.jpg)
