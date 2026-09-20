# 影片廣告沒有觀看：先確認哪一層卡住

## 取得可比較的現況

先鎖定使用者指定的一般帳戶及 campaign；manager 帳戶不是投放帳戶。查詢前讀取當前 resource metadata，確認欄位可選取、可篩選及相容性，並使用有限筆數。不要直接套用 Search 專用的 impression-share 查詢到 Video。[GAQL query structure](https://developers.google.com/google-ads/api/docs/query/structure)

按問題選取欄位，不必每次匯出整個帳戶：

| 問題 | 要核對的資料 |
| --- | --- |
| 查的是誰、用什麼單位？ | `customer.currency_code`、`customer.time_zone`、帳戶狀態、campaign / ad group / ad 識別 |
| 現在能不能投？ | campaign 與 ad 狀態、policy / review 狀態、開始及結束日期、排程；有付款警示才進一步查相關限制 |
| 預算還剩多少？ | campaign 綁定的 budget、period、amount / total amount、同一 campaign 的已花費金額 |
| 實際用哪個出價？ | bidding strategy type 及其生效欄位；不要只讀名稱相似的 legacy 欄位 |
| 可以投給誰、在哪裡？ | 地區與 location options、語言、人口統計及 Unknown、audience、expansion、裝置、network、格式、frequency caps |
| 是否真的投過？ | 明確日期區間內的 impressions、views、clicks、cost；註明帳戶時區及資料取得時間 |

設定查詢與成效查詢分開。零活動的報表可能不回傳資料列；空結果、明確的零、查詢失敗、未取到資料，分別回報。不要由「沒有 recommendations」推論沒有問題，也不要由 eligible 狀態推論付款正常。

## 金額與生效欄位

`micros / 1_000_000` 才是帳戶幣別金額，計算使用整數或 Decimal，避免二進位浮點誤差。UI 只顯示 `$` 時不能判斷是哪個幣別。

- `CUSTOM_PERIOD` 搭配 `total_amount_micros` 是整段期間的總額；不能把 `amount_micros = 0` 解讀為零預算。
- 總額包含這個 campaign 已花費的部分，不是額外新增的額度。剩餘可用額度需扣掉對應已花費金額。
- `TARGET_CPV` 應核對當前 schema 的 `ad_group.target_cpv_micros`；同時存在的 `cpv_bid_micros` 不一定生效。
- 每日平均預算與總預算的花費規則不同。不要為了符合一句「總共花多少」就擅自轉換預算類型或複製 campaign。[Campaign total budgets](https://support.google.com/google-ads/answer/10486938?hl=en)

## 不把序列化預設值當成設定

MCP 或 protobuf 轉成 JSON 後，未設定的 scalar 可能顯示 `0.0`。例如所有 device bid modifier 都是零，尚不能證明所有裝置被排除。

若欄位支援篩選，分別檢查 `IS NULL` 與明確 `= 0` 的結果，或查實際 UI 的裝置選取狀態。保留三種結果：未設定、明確設定為零、尚無法判定。若 API 序列化值與 UI 衝突，不要以同一份模糊回應當成雙重驗證。

Audience 的名稱也不是其定義。舊 segment 查不到 members 時，先確認支援範圍、型別與 UI，不要直接認定它是空的或已失效。

## 形成診斷，不先提高花費

先分清楚日期尚未到／已結束、廣告待審或受限、預算不足、出價缺乏競爭力、受眾或版位限制等不同可能。只有可觀測證據支持時才稱為原因；其餘列為假設及下一個最小檢查。

廣告尚在審查，不代表提高出價可以解除審查。受眾狹窄，也不代表必須放寬使用者明確選定的買家條件。提出調整時說明預期作用、代價與驗證方式，而不是一次改掉所有設定。

設定成功之後，仍需以後續成效資料確認投放。記錄資料延遲或審查狀態；不要用空白畫面承諾「已開始有觀看」。
