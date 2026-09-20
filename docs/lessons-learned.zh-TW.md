# Google Ads MCP 常見誤判

安裝卡住時，先找出失敗的位置：指令、檔案、登入、帳戶、查詢，還是 AI 客戶端。

| 看到的結果 | 容易誤判成 | 正確處理 |
| --- | --- | --- |
| Google Ads skill 已安裝 | AI 已能查帳戶 | 另外安裝 MCP、完成 ADC 登入並註冊客戶端 |
| Server 顯示 `stdio` 後等待 | 程式卡住 | 由 MCP 客戶端啟動，測握手與工具清單 |
| `.env` 出現憑證欄位名稱 | 認證已備妥 | 檢查非空值與 ADC，再做唯讀查詢 |
| 舊技能要求 Developer Token | 新使用者也得申請 | 依目前 Cloud 專案 access level 流程設定 |
| `Unknown tool` 或參數錯誤 | Server 安裝壞了 | 讀取 `tools/list` 與 input schema |
| `gcloud` 找不到 | Google 登入失敗 | 先處理 CLI 安裝或 PATH |
| 檔案路徑在空格處截斷 | JSON 內容有問題 | 用雙引號包住完整路徑 |
| Google 登入完成 | 所有 Ads 帳戶都能查 | 逐一確認目標帳戶的權限與啟用狀態 |
| 第一個帳戶查詢失敗 | 整組登入無效 | 區分帳戶停用、manager 與一般帳戶 |
| 工具沒有拋出例外 | 已查到 campaigns | 解析回應，檢查 `isError` 並確認筆數 |
| 獨立測試程式成功 | Codex 已接通 | 檢查客戶端註冊，再從對話內呼叫工具 |

## 排錯順序

先用 `command -v` 確認工具存在，再確認 OAuth JSON 的實際位置。登入完成後，依 server 當前的工具清單組參數，選擇可用的一般帳戶做小量查詢。最後回到要使用的 AI 客戶端，確認它也能呼叫工具。

每次只修正已定位的問題。例如，路徑缺引號就補引號；帳戶停用就查帳戶狀態。重裝 server 無法解決這兩種錯誤。

## 怎樣才算查詢成功

回傳空陣列代表成功查到零筆；回傳無法解析的格式則應報錯。兩者不能混在一起。

測試至少要記錄實際呼叫的工具、可解析的結果與筆數。MCP 連線成功、Google API 查詢成功、AI 客戶端整合成功，分別驗證、分別回報。

[完整安裝教學](../skills/google-ads-mcp-setup-guide/references/tutorial.zh-TW.md) · [錯誤排除](../skills/google-ads-mcp-setup-guide/references/troubleshooting.zh-TW.md)
