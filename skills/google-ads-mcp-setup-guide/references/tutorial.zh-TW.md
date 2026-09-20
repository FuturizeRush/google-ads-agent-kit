# Google Ads MCP 安裝教學

接通後，你可以請 AI 列出 Google Ads 帳戶、查詢廣告活動，再逐步加入報表分析。

以下使用 macOS、zsh 與 Codex，從安裝工具走到客戶端內的實際查詢。查證日期：2026-09-20。

## 1. 準備工具與帳號

你需要可登入 Google Ads 的 Google 帳號、可管理的 Google Cloud 專案，以及 AI 客戶端。

| 元件 | 負責什麼 |
| --- | --- |
| Google Cloud CLI | 提供 `gcloud` 指令，用來建立本機 Google 登入授權 |
| Google Ads skill | 提供 AI 操作指引 |
| Google Ads MCP server | 提供 AI 可以呼叫的 Google Ads 查詢工具 |
| ADC | 保存本機登入授權，供 MCP 使用 |
| Codex、Claude Code 等客戶端 | 啟動 MCP server，讓對話能呼叫工具 |

`gcloud` 和 Google Cloud CLI 是同一套安裝。Skill、MCP server 和登入授權則各有自己的步驟。

```text
你 → AI 客戶端 → 本機 MCP server → Google Ads API
                   使用 ADC 登入
```

這條連線使用 `stdio`：客戶端啟動本機 MCP 程式並交換訊息，無須架網站或開放連接埠。[官方 server 說明](https://github.com/googleads/google-ads-mcp)

先逐行檢查已有的工具，缺少哪項再補裝：

```bash
command -v brew
command -v gcloud
python3 --version
pipx --version
node --version
npm --version
command -v codex
```

Node.js / npm 用來安裝 skills；Python / pipx 用來安裝 MCP。新環境建議使用 Python 3.12 以上版本，實際需求以套件安裝器為準。

## 2. 安裝 Google Cloud CLI

尚未安裝 Homebrew，先依 [Homebrew 官網](https://brew.sh/)完成安裝，再開啟新終端機。

```bash
brew update
brew install --cask gcloud-cli
```

驗證安裝：

```bash
gcloud help version
gcloud version --quiet
```

看到 Google Cloud SDK 版本即表示 `gcloud` 可執行。若仍顯示 `command not found`，先開新終端機；還是找不到時，依安裝器的 PATH 提示設定。

Homebrew 會安裝必要依賴，無須順便升級其他無關套件。[Google 的 Homebrew 安裝說明](https://docs.cloud.google.com/sdk/docs/downloads-homebrew)

Windows / Linux 使用者請改用[對應平台的安裝步驟](https://docs.cloud.google.com/sdk/docs/install-sdk)。

## 3. 安裝 Google Ads skills

缺少 pipx 或 Node.js 時，安裝需要的項目：

```bash
brew install pipx node
pipx ensurepath
```

開新終端機，確認 `pipx --version`、`python3 --version`、`node --version` 可執行。若 Python 不符合套件需求，可先安裝合適版本，再用 pipx 的 `--python` 指定。[pipx 安裝說明](https://pipx.pypa.io/stable/installation/)

在工作專案目錄安裝 Google Ads 官方 skills：

```bash
npx --yes skills add google/skills --skill google-ads-api-quickstart google-ads-api-mcp-setup google-ads-api-account-diagnostics --agent codex
```

| Skill | 用途 |
| --- | --- |
| `google-ads-api-quickstart` | API 起步與認證設定 |
| `google-ads-api-mcp-setup` | MCP 安裝與連接 |
| `google-ads-api-account-diagnostics` | 安裝完成後分析帳戶問題，可選 |

需要 gcloud 操作指引時，另外安裝：

```bash
npx --yes skills add google/skills --skill gcloud --agent codex
```

確認安裝結果：

```bash
npx --yes skills list --agent codex
```

上述為專案級安裝。在該專案開啟新對話，讓客戶端載入技能。Claude Code 使用者把 `--agent codex` 改成 `--agent claude-code`。

日後更新指定技能：

```bash
npx --yes skills update google-ads-api-quickstart google-ads-api-mcp-setup google-ads-api-account-diagnostics
```

使用 `--skill` 指定名稱，可避免安裝整套 Google skills。安裝器參數有變動時，查看 `npx --yes skills --help`。[Google 官方技能](https://developers.google.com/google-ads/api/docs/developer-toolkit/agent-skills)、[skills CLI](https://github.com/vercel-labs/skills)

## 4. 設定 Google Cloud 專案

進入 [Google Cloud Console](https://console.cloud.google.com/)，建立或選擇專案。API、存取等級與 OAuth client 都設在同一個專案。

1. 在 **API Library** 搜尋 **Google Ads API**，開啟服務頁並按 **Enable**。
2. 到 Google Ads API 的 **Overview** 查看 access level。
3. 查詢實際投放帳戶需要 production 存取權限。若目前只有 Test，可依畫面的 **Upgrade access level → Explorer → Apply for access** 申請。

Test 僅能存取測試帳戶；Explorer、Basic、Standard 支援 production 存取。按下 Enable 後，仍需確認 access level。[存取等級](https://developers.google.com/google-ads/api/docs/api-policy/access-levels)

Google 自 2026-09-09 起改由 Cloud 專案管理 API 存取權限。新使用者直接在 Cloud Console 設定，無須到 MCC 的 API Center 申請 Developer Token。[政策變更](https://developers.google.com/google-ads/api/docs/api-policy/developer-token)

## 5. 建立 OAuth client 並下載 JSON

OAuth client 識別應用程式，下一步的登入則授權它存取你的 Google 帳戶。

1. 開啟 **Google Auth Platform**。部分介面從 **APIs & Services → OAuth consent screen** 進入。
2. 填寫應用程式名稱與必要聯絡資訊。個人測試可使用 **External / Testing**，並把登入 Google Ads 的帳號加入 **Test users**。組織環境沿用既有政策。
3. 到 **Clients**，或 **APIs & Services → Credentials → Create credentials → OAuth client ID**。
4. 選擇 **Desktop app**，建立後下載 JSON。
5. 將檔案命名為 `client_secrets.json`，放在 Downloads，保留在 Git repo 之外。

JSON 包含 client ID 與 client secret；只把 client ID 字串存成檔案無法代替它。已有合適的 Desktop client，可沿用原本的下載檔。[OAuth 設定](https://developers.google.com/google-ads/api/docs/oauth/cloud-project)

先確認檔案位置：

```bash
test -f "$HOME/Downloads/client_secrets.json" && printf 'JSON file exists\n'
```

沒有顯示訊息時，檢查下載檔名與資料夾，再繼續。

## 6. 登入並建立 ADC

查看目前版本的登入參數：

```bash
gcloud help auth application-default login
```

下面指令會替換既有的本機 ADC。若其他工具也使用 ADC，先確認要共用的 Google 身分。

由帳戶擁有者在本機終端機貼上這一整行：

```bash
gcloud auth application-default login --scopes="https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform" --client-id-file="$HOME/Downloads/client_secrets.json" --quiet
```

瀏覽器開啟後，登入有 Google Ads 權限的帳號，閱讀授權項目並同意。Google 若要求兩步驟驗證或 passkey，依畫面完成。`--quiet` 不會略過瀏覽器授權。[認證安全要求](https://developers.google.com/google-ads/api/docs/oauth/security-requirements)

成功訊息包含 `Credentials saved to file`。macOS / Linux 的 ADC 預設位置為：

```text
$HOME/.config/gcloud/application_default_credentials.json
```

MCP 可直接使用這份 ADC，無須手動複製 refresh token。一般也不必設定 `GOOGLE_APPLICATION_CREDENTIALS`；如果已設定，它指向的檔案會優先使用。[ADC 搜尋順序](https://docs.cloud.google.com/docs/authentication/application-default-credentials)

登入時留意三件事：

- `gcloud auth login` 與 `gcloud auth application-default login` 用途不同；此流程需要後者。
- `adwords` 與 `cloud-platform` 並非唯讀 OAuth scope。前者授權 Ads 存取，後者涉及你已有 IAM 權限的 Cloud 資源；本教學只呼叫查詢工具。
- External / Testing 應用程式使用這些 scope 時，refresh token 通常七天到期。長期使用須依 Google 政策處理應用程式狀態與驗證。[到期規則](https://developers.google.com/identity/protocols/oauth2#expiration)

## 7. 安裝 Google Ads MCP server

```bash
pipx install google-ads-mcp
pipx list
command -v google-ads-mcp
```

確認清單包含 `google-ads-mcp`，並取得可執行檔路徑。已安裝時只需檢查；需要更新才執行 `pipx upgrade google-ads-mcp`。本次實測版本為 0.0.3。

手動執行 `google-ads-mcp` 後停在畫面上，是在等待 MCP 訊息。檢查結束按 Ctrl-C，之後交給 AI 客戶端啟動。此版本的 `--help` 也會啟動 server，因此驗收請用下一節的連線測試。

看見 `No local tools_config.yaml found; using the bundled default configuration`，表示使用內建設定，可繼續。[官方 server 設定](https://github.com/googleads/google-ads-mcp)

## 8. 註冊到 AI 客戶端

以下使用 Codex CLI。尚未安裝 Codex，可依[官方安裝文件](https://developers.openai.com/codex/cli/)設定，或改用目前客戶端的 MCP 設定介面。

先檢查現有設定和指令路徑：

```bash
codex mcp list
codex mcp add --help
command -v google-ads-mcp
```

取得可執行檔路徑，並確認沒有要保留的同名設定後，執行：

```bash
codex mcp add google-ads -- "$(command -v google-ads-mcp)"
codex mcp get google-ads
```

這會以真實可執行檔路徑註冊 server，沿用目前 OS 使用者的 ADC。

使用 JSON 設定的客戶端，可參考 repo 根目錄的 `examples/mcp-client.example.json`，將 command 換成自己的可執行檔路徑。註冊後重新載入 MCP 或開啟新對話；客戶端若要求重啟，再退出重開。

透過 Manager / MCC 存取子帳戶時，可能還需要在 MCP 的啟動環境設定 `GOOGLE_ADS_LOGIN_CUSTOMER_ID`。它填 manager 的十位數 ID；查詢中的 `customer_id` 填目標子帳戶 ID。兩者去掉連字號，依實際帳戶關係設定。[存取模型](https://developers.google.com/google-ads/api/docs/oauth/access-model)

## 9. 驗證連線與查詢

下載測試程式：

```bash
git clone https://github.com/FuturizeRush/google-ads-agent-kit.git
cd google-ads-agent-kit
```

已經有 repo，直接進入目錄即可。若只安裝 skill，使用該 skill 內 `scripts/mcp_smoke_test.py` 的路徑。

先測 MCP 連線，再查 Google Ads：

```bash
python3 skills/google-ads-mcp-setup-guide/scripts/mcp_smoke_test.py
python3 skills/google-ads-mcp-setup-guide/scripts/mcp_smoke_test.py --live
```

`--live` 讀取 customer / campaign metadata，最多檢查五個直接可存取帳戶，每個一般帳戶最多查五筆 campaigns。輸出保留結果與筆數，省略帳戶身分及廣告內容。

| 結果 | 下一步 |
| --- | --- |
| `TRANSPORT_ONLY` | MCP 連線成功，可繼續執行 `--live` |
| `customer_not_enabled` | 檢查該帳戶啟用狀態，或選擇其他可用帳戶 |
| `SKIPPED_MANAGER_SELECT_CHILD` | 選擇 manager 底下的目標子帳戶 |
| `PASS_EMPTY` | 查詢成功，零筆資料 |
| `PASS_WITH_ROWS` | 查詢成功，有資料 |
| `NO_CLIENT_QUERY_VERIFIED` | 尚無一般帳戶完成 campaign 查詢，依錯誤類別排查 |
| `host_integration: NOT_TESTED` | 進入下一步，在 AI 客戶端內驗證 |

若只有 MCC 出現在清單，先確認目標子帳戶及 manager 路由，再用 `--live --customer-id YOUR_CLIENT_ID` 指定目標。清單只包含直接可存取的帳戶；測試程式不會自動遍歷整棵帳戶樹。

## 10. 從 AI 對話完成最後一次查詢

在已註冊 MCP 的客戶端輸入：

```text
使用 Google Ads MCP 列出我可直接存取的帳戶。
有多個可用帳戶時，先讓我選擇。
讀取 campaign metadata，再查 campaign.id、campaign.name、campaign.status，最多 5 筆。
回報實際使用的工具、回傳筆數與結果，不修改廣告。
```

本次版本的工具名稱為 `customers_list_accessible_customers`、`metadata_get_resource_metadata`、`search_search`。metadata 使用 `resource_name`；search 使用 `customer_id`、`fields`、`resource` 等參數。客戶端應讀取實際 input schema，避免套用舊版參數。

對話內能呼叫工具並取得可解析的查詢結果，就完成了整條連線。零筆也是有效結果；若只有獨立測試成功，回到第 8 步檢查客戶端設定。

[錯誤排除](troubleshooting.zh-TW.md) · [來源與版本](sources.md)
