# Google Ads Agent Kit

讓 AI agent 接通 Google Ads MCP，診斷影片廣告投放，並安全執行已授權的設定調整。

提供可安裝的 agent skills、繁體中文教學與唯讀連線測試。安裝教學以 macOS 和 Codex 為主；Claude Code 可使用相同 skills。

| Skill | 何時使用 |
| --- | --- |
| [google-ads-mcp-setup-guide](skills/google-ads-mcp-setup-guide/SKILL.md) | 安裝 gcloud、設定 ADC、接通 MCP、排除連線錯誤 |
| [google-ads-video-ops](skills/google-ads-video-ops/SKILL.md) | 沒有觀看、看不懂預算幣別、檢查 CPV／受眾／頻率，以及驗證已授權的修改 |

## 安裝 skill

準備好 Node.js 與 npm，在工作專案中執行：

```bash
npx --yes skills add FuturizeRush/google-ads-agent-kit --skill google-ads-mcp-setup-guide --agent codex
npx --yes skills add FuturizeRush/google-ads-agent-kit --skill google-ads-video-ops --agent codex
```

按需要執行其中一行或兩行。Claude Code 使用者把 `--agent codex` 改成 `--agent claude-code`。這一步安裝操作指引與附帶資源；gcloud、Google 授權和 MCP 設定由後續流程完成。

開啟新的 agent 對話，輸入：

```text
使用 google-ads-mcp-setup-guide，幫我接通 Google Ads MCP。
先檢查已有的工具與設定，再補齊缺少的步驟。
最後從目前客戶端做一次唯讀查詢，回報結果。
```

已有可用帳戶連線，要檢查影片廣告：

```text
使用 google-ads-video-ops，檢查我指定的 Video campaign 為什麼沒有觀看。
先確認幣別、預算類型、日期、出價及審查狀態，再評估受眾。
保留我的客群限制，提出有依據的建議，先不要修改。
```

操作 skill 不附帶寫入權限或自動調價程式。修改前需有明確授權及可用的寫入介面；MCP 的唯讀工具不能代替它。公開內容不提供固定的預算、CPV 或人口條件作為通用預設。

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
