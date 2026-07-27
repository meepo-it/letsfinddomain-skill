# Porkbun API 配置

[English](setup.md) · **简体中文**

Porkbun 有两条可用路径：公开 TLD 价格列表不需要凭据；使用账号查询域名可用性则需要 API Key 和 Secret。

## 1. 打开 API Access

登录 [Porkbun](https://porkbun.com/account)，打开
[Account → API Access](https://porkbun.com/account/api)。

## 2. 创建 API Key 对

创建新的 API Key 和 Secret。请立即复制 Secret；如有需要，可以按 IP 地址或域名限制这个 Key。把两个值写入 skill 的 `.env`：

```dotenv
PORKBUN_API_KEY=你的_api_key
PORKBUN_SECRET_API_KEY=你的_secret_api_key
```

查询程序只使用域名可用性读取接口。Porkbun 的公开价格列表无需 Key，仍然可以作为默认参考价格来源。

## 3. 验证配置

回到 `/letsfinddomain-skill`，直接输入：

```text
检查 example.com，并告诉我可用性和续费价格。
```

`example.com` 应显示为 `taken`。Porkbun 的可用性接口一次查询一个域名，因此大批候选会由 skill 自动限速处理。

![Porkbun API 文档](assets/api-docs.png)
