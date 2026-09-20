# 驗證紀錄

日期：2026-09-20

| 檢查 | 結果 |
| --- | --- |
| 離線單元測試 | 36 個測試通過，涵蓋回應解析、錯誤處理、查詢上限與公開檔案規則 |
| Skill 格式 | frontmatter 與必要欄位檢查通過 |
| Skill 安裝 | 獨立目錄試裝成功，附帶腳本與參考文件完整 |
| 文件檢查 | 17 個相對連結與 23 段 shell 指令語法通過 |
| 公開檔案 | 18 個允許發佈的檔案通過內容掃描與本機憑證比對；Gitleaks 未檢出洩漏 |
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

[套件版本與來源](../skills/google-ads-mcp-setup-guide/references/sources.md) · [發佈安全檢查](../SECURITY.md)
