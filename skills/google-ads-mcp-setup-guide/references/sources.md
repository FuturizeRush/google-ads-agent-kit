# 來源與版本

查證日期：2026-09-20。

## 官方資料

| 主題 | 來源 | 用來確認 |
| --- | --- | --- |
| Google Ads 官方 skills | [Developer toolkit](https://developers.google.com/google-ads/api/docs/developer-toolkit/agent-skills)、[google/skills](https://github.com/google/skills) | skill 的用途與來源 |
| skills 安裝器 | [vercel-labs/skills](https://github.com/vercel-labs/skills) | `--skill`、`--agent` 與更新語法；本機 CLI help 優先 |
| gcloud 安裝 | [Homebrew 方法](https://docs.cloud.google.com/sdk/docs/downloads-homebrew)、[各平台安裝](https://docs.cloud.google.com/sdk/docs/install-sdk) | 各平台安裝步驟 |
| gcloud login 指令 | 本機 `gcloud help auth application-default login`；[可閱讀的官方 reference](https://docs.cloud.google.com/sdk/gcloud/reference/auth/application-default/login) | `--client-id-file`、`--scopes` 與 ADC 覆寫行為 |
| ADC | [Application Default Credentials](https://docs.cloud.google.com/docs/authentication/application-default-credentials) | 預設憑證位置與環境變數的搜尋順序 |
| OAuth 設定 | [Google API Console project](https://developers.google.com/google-ads/api/docs/oauth/cloud-project) | Cloud 專案、consent、Desktop client |
| OAuth 到期 | [Refresh token expiration](https://developers.google.com/identity/protocols/oauth2#expiration) | External / Testing 的七天限制 |
| Google Ads 認證 | [Security requirements](https://developers.google.com/google-ads/api/docs/oauth/security-requirements) | 登入時可能要求 2SV / passkey |
| Developer Token 變更 | [Migration notice](https://developers.google.com/google-ads/api/docs/api-policy/developer-token) | 2026-09-09 起轉為 Cloud project access levels |
| API 權限 | [Access levels](https://developers.google.com/google-ads/api/docs/api-policy/access-levels) | Test 與 production 存取的差異 |
| MCC 存取 | [Access model](https://developers.google.com/google-ads/api/docs/oauth/access-model) | 直接存取、manager routing、target account |
| Google Ads MCP | [官方 repository](https://github.com/googleads/google-ads-mcp)、[PyPI](https://pypi.org/project/google-ads-mcp/) | 安裝 package、stdio、ADC、tool namespacing |
| Codex 設定 | 本機 `codex mcp add --help` / `get --help`；[官方文件](https://developers.openai.com/codex/mcp/) | Codex MCP 註冊語法 |

## 已核對的版本

- `googleads/google-ads-mcp`：[`7a40eae9655194a84d5291c63af817bb20d02ea8`](https://github.com/googleads/google-ads-mcp/tree/7a40eae9655194a84d5291c63af817bb20d02ea8)
- `google/skills`：[`18152e0d310e4d7047e9c2ec25a37b0d22d6893e`](https://github.com/google/skills/tree/18152e0d310e4d7047e9c2ec25a37b0d22d6893e)
- 實測安裝：Google Cloud SDK 585.0.0；google-ads-mcp 0.0.3；google-ads 32.0.0；FastMCP 4.0.5；mcp 2.2.0。
- 0.0.3 的 package metadata 宣告 Python `>=3.10`；本教學建議使用 3.12 以上的新環境。依賴套件也有版本需求，安裝器的解析結果與目前官方支援範圍仍需檢查。

版本升級後，重新檢查工具清單與輸入格式。

## 文件與實際行為不同時

舊版技能可能仍要求 Developer Token，或使用不同的 metadata / search 參數。政策查當前官方正文；工具名稱與參數查正在執行的 server。

搜尋摘要與頁首自動摘要可能保留舊規則，遇到矛盾時讀完整正文。
