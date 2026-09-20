# 驗證紀錄

日期：2026-09-20

| 檢查 | 結果 |
| --- | --- |
| 離線單元測試 | 44 個測試通過；涵蓋 MCP 解析與查詢上限、公開檔案規則、暫存內容／歷史洩漏、長識別碼與私有資料比對 |
| Skill 格式 | 兩個 skills 的 frontmatter 與必要欄位檢查通過 |
| Skill 安裝 | 兩個 skills 在獨立目錄試裝，附帶腳本與參考文件完整 |
| 文件檢查 | 相對連結與 shell 指令語法檢查通過 |
| 公開檔案 | 24 個 allowlisted 檔案；掃描工作檔、暫存 blob、Git 歷史及本機私有資料，另跑 Gitleaks；未檢出洩漏 |
| Video 操作判斷 | 兩個獨立 agent 完成[合成情境](../tests/video-ops-scenarios.md)：唯讀零觀看診斷、授權修改與不明 Save 結果；未連線或更動帳戶 |
| MCP 連線 | 官方 server 的 stdio 握手與工具發現成功 |
| Google Ads API | 使用既有 ADC，完成一般帳戶的唯讀 campaign 查詢 |
| Codex 對話整合 | 尚未實測；獨立測試程式不驗證客戶端註冊 |

## 重跑離線測試

```bash
python3 -B -m unittest discover -s tests -v
python3 scripts/check_public_tree.py --history
```

測試使用合成資料，不需 Google 帳號。GitHub Actions 另外執行 Gitleaks 檔案與歷史掃描；各次結果見 repository 的 Actions 頁面。

## 實測範圍

本機流程在 macOS Apple silicon 與 zsh 驗證。Windows / Linux 的完整安裝與其他 AI 客戶端尚未實測；CI 的 Linux 離線測試不代表 Google 登入或客戶端整合已通過。

Google API 測試只驗證連線與少量查詢，不涵蓋所有帳戶、廣告報表或完整 MCC 階層。

Video skill 是操作指引，不是已自動化測試所有 Ads UI 的程式。離線情境通過不證明任何實際 campaign 已核准、開始投放或產生轉換；實際操作仍需逐欄讀回。

[套件版本與來源](../skills/google-ads-mcp-setup-guide/references/sources.md) · [發佈安全檢查](../SECURITY.md)
