# Google Ads Agent Kit

讓 AI agent 帶你安裝 Google Ads MCP、完成 Google 登入，並查到第一筆廣告活動資料。

提供可安裝的 agent skill、繁體中文教學與唯讀連線測試。適用 macOS，主線使用 Codex；Claude Code 可使用同一份 skill。

## 安裝 skill

準備好 Node.js 與 npm，在工作專案中執行：

```bash
npx --yes skills add FuturizeRush/google-ads-agent-kit --skill google-ads-mcp-setup-guide --agent codex
```

Claude Code 使用者把 `--agent codex` 改成 `--agent claude-code`。這一步安裝操作指引與測試腳本；gcloud、Google 授權和 MCP 設定由後續流程完成。

開啟新的 agent 對話，輸入：

```text
使用 google-ads-mcp-setup-guide，幫我接通 Google Ads MCP。
先檢查已有的工具與設定，再補齊缺少的步驟。
最後從目前客戶端做一次唯讀查詢，回報結果。
```

## 從零開始

[完整安裝教學](skills/google-ads-mcp-setup-guide/references/tutorial.zh-TW.md) 依序完成：

1. 安裝 Google Cloud CLI，也就是提供 `gcloud` 指令的工具套件。
2. 選擇性安裝 Google Ads 官方 skills。
3. 設定 Google Cloud 專案、OAuth client 與 ADC 登入。
4. 安裝官方 Google Ads MCP server，註冊到 AI 客戶端。
5. 列出帳戶並查詢 campaigns，確認整條連線可用。

已經遇到錯誤，直接查[錯誤排除](skills/google-ads-mcp-setup-guide/references/troubleshooting.zh-TW.md)或[常見誤判](docs/lessons-learned.zh-TW.md)。

## 測試連線

完成 MCP 安裝與 ADC 登入後：

```bash
git clone https://github.com/FuturizeRush/google-ads-agent-kit.git
cd google-ads-agent-kit
python3 skills/google-ads-mcp-setup-guide/scripts/mcp_smoke_test.py
python3 skills/google-ads-mcp-setup-guide/scripts/mcp_smoke_test.py --live
```

第一個測試檢查 MCP 連線和工具清單；`--live` 會呼叫 Google Ads API，最多檢查五個帳戶，每個一般帳戶最多查五筆 campaigns。測試不修改廣告，不輸出帳戶 ID、廣告名稱或憑證。

| 結果 | 意義 |
| --- | --- |
| `TRANSPORT_ONLY` | MCP 連線成功，尚未查帳戶 |
| `PASS_EMPTY` | 查詢成功，零筆資料 |
| `PASS_WITH_ROWS` | 查詢成功，有資料 |
| `LIVE_QUERY_VERIFIED` | 至少一個一般帳戶完成 campaign 查詢 |
| `host_integration: NOT_TESTED` | 還需在 AI 客戶端內呼叫工具 |

## 開發與維護

```bash
python3 -B -m unittest discover -s tests -v
python3 scripts/check_public_tree.py
```

離線測試不需要 Google 帳號。[驗證紀錄](docs/verification.md)列出實測範圍；[安全說明](SECURITY.md)列出憑證保存與發佈檢查方式。

[來源與版本](skills/google-ads-mcp-setup-guide/references/sources.md) · [MIT License](LICENSE)

社群維護，非 Google 或 OpenAI 官方專案。
