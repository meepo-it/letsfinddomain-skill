# Spaceship API 配置

[English](setup.md) · **简体中文**

Spaceship 的可用性接口一次最多支持查询 20 个域名，因此作为默认可用性 Provider。

## 1. 打开 API Manager

登录 [Spaceship](https://www.spaceship.com/)，打开
[API Manager](https://www.spaceship.com/application/api-manager/)。

## 2. 创建凭据

创建新的 API Key 和 Secret。请妥善保管，Secret 可能只显示一次。把它们写入仓库的 `.env` 文件：

```dotenv
SPACESHIP_API_KEY=你的_key
SPACESHIP_API_SECRET=你的_secret
```

查询程序只使用域名可用性读取操作。

## 3. 验证配置

回到 `/letsfinddomain-skill`，输入：

```text
检查 example.com，并告诉我可用性和续费价格。
```

`example.com` 应显示为 `taken`。

![Spaceship API 文档](assets/api-docs.jpg)
