# Cloudflare Registrar API 配置

[English](setup.md) · **简体中文**

Cloudflare Registrar 查询需要账号 ID 和 API Token。目前 Registrar API 只支持部分域名后缀。

## 1. 准备账号

打开 Cloudflare 控制面板并复制目标账号 ID。根据官方的
[Registrar API 文档](https://developers.cloudflare.com/registrar/registrar-api/)，还需要准备账单资料、默认付款方式、注册人联系人，并接受注册协议。

## 2. 创建 API Token

打开 **My Profile → API Tokens → Create Token**，按照官方文档授予 Registrar API 所需权限。建议将两个值设置为系统环境变量，具体见[跨平台配置](../../../references/environment.md#system-environment-variables)：

```dotenv
CLOUDFLARE_ACCOUNT_ID=你的_account_id
CLOUDFLARE_API_TOKEN=你的_api_token
```

不要提交 Token 或包含账号信息的截图。

## 3. 验证配置

回到 `/letsfinddomain-skill`，输入：

```text
检查 example.com，并告诉我可用性和续费价格。
```

结果应显示 `taken`。不支持的后缀会显示为 `unsupported`，不会被误报为可用。

![Cloudflare Registrar API 文档](assets/registrar-api-docs.jpg)
