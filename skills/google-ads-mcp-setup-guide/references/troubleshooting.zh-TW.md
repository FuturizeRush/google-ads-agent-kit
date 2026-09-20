# Google Ads MCP 錯誤排除

依畫面上的錯誤找原因，再執行對應的下一步。

| 畫面或症狀 | 意義 | 下一步 |
| --- | --- | --- |
| `zsh: command not found: gcloud` | CLI 未安裝，或目前 shell 找不到它 | `command -v gcloud`；依安裝步驟補裝或更新 PATH |
| Homebrew 顯示 installed，shell 仍找不到 | 安裝完成但 shell 環境尚未更新 | 新開終端機，再查可執行檔位置 |
| `Cannot read file: .../Google`，實際資料夾叫 `Google Ads` | 路徑中的空格把參數切開 | 用雙引號包住整個路徑 |
| JSON file 不存在 | 範例檔名、實際下載檔名或資料夾不同 | 先確認檔案，不能只照抄範例路徑 |
| 指令裡出現 `[https://...](https://...)` | Markdown 連結被當成 shell 文字 | 從 code block 的複製按鈕取純文字 |
| `Your default credentials were not found` | 程式找不到可用 ADC | 檢查 ADC 登入是否完成，以及 host 的 OS 使用者 / 環境 |
| `.env` 有 Client ID 和 Secret，仍缺 ADC | 應用程式身分不等於使用者登入 | 使用 ADC 流程；不要假設 server 自動讀 `.env` |
| Google 的 access denied / Testing user 限制 | OAuth app 的測試名單或組織政策不允許該使用者 | 確認目前選到的 Google 帳號與 Test users 設定 |
| `invalid_grant` | 授權過期、撤銷或受 session policy 影響 | 重新確認帳號與 scope，必要時由本人重新授權 |
| `CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION` | Cloud 專案的 API 存取等級不足 | 在 Google Ads API Overview 檢查 Test / Explorer 等級 |
| `USER_PERMISSION_DENIED` | 該身分無法用目前路徑存取目標帳戶 | 核對 user、target client ID、MCC 路由與帳戶權限 |
| 帳戶 not yet enabled / deactivated | 帳戶本身尚未啟用或已停用 | 看該帳戶 UI 狀態；不要改 token 或自動啟用帳戶 |
| `Unknown tool` | 名稱或 namespace 與實際 server 不符 | 先 `tools/list` 再呼叫 |
| `resource_name` missing、`resource` unexpected | 參數名稱用錯 | 依 input schema 調整 |
| 手動執行 server 後一直等待 | stdio server 等候 host 訊息 | 由 MCP host 啟動；手動檢查後 Ctrl-C |
| 工具回傳成功但內容是空陣列 | 查詢成功、零筆資料 | 報告零筆，不宣稱已有 campaigns |
| 獨立 probe 成功、AI 對話沒工具 | host 未註冊、未載入或環境不同 | 檢查該 host 的 MCP 設定，並在 host 內實測 |
| 另一個 AI CLI 未登入 | 只代表那個客戶端尚未準備好 | 使用原本選定的客戶端，不必為測 MCP 先登入另一個產品 |

## 空格與 Markdown 的正確處理

路徑包含空格時應保持整段為一個參數：

```bash
gcloud auth application-default login --scopes="https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform" --client-id-file="$HOME/Documents/Google Ads/client_secrets.json" --quiet
```

這個路徑只示範引號用法，必須換成確實存在的檔案。執行前先依主教學確認 ADC 覆寫影響，並看 `gcloud help auth application-default login`。

選項直接寫 `--scopes`。多行 shell 指令的反斜線放在上一行尾端，選項前不用加。

## 帳戶識別與 MCC

Customer ID 是 Ads 帳戶的十位數字，可在 Google Ads 帳戶介面找到；傳給 API 時去掉連字號。`customer_id` 是要查詢的目標；`login_customer_id` 是透過 manager 存取時的登入路由。它們可能不同，也都不是 Google Cloud project ID。[Customer ID 說明](https://support.google.com/google-ads/answer/1704344)、[Google Ads 存取模型](https://developers.google.com/google-ads/api/docs/oauth/access-model)

不要把 list 的第一項固定當成目標。列得出帳戶不代表該帳戶已啟用；MCC 也不是投放廣告的 client。具體要查哪個帳戶不明確時，先辨識目標再查。公開 issue 裡不要放真實 ID。

## 測試只回傳 `api_or_tool_error`

`api_or_tool_error` 表示程式尚未辨識錯誤原因。原始 Google 錯誤及 server stderr 可能包含帳戶或查詢內容，因此測試程式省略這些輸出。

在本機檢查原始工具回應，確認原因後再處理。分享錯誤時，先移除憑證、姓名、email、帳戶及 campaign ID。修改測試程式時，保留 `isError` 與格式檢查；解析失敗必須回報錯誤。

更多當前限制與官方來源見 [sources.md](sources.md)。
