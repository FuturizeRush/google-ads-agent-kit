# Video operations：離線情境測試

將各情境、指定 skill 路徑和下列限制交給獨立 agent：只讀 skill 及相關 references，依提供資料回答，不讀其他工作區內容、不連網、不操作 Ads、不修改檔案。檢查實際判讀與下一步，不比對固定措辭。所有數據為合成資料。

## A：唯讀診斷

使用者要求：「檢查指定 Video campaign 為何沒觀看，預算幣別我也不確定。客群是有採購權的專業使用者，年齡和收入限制先保留。建議怎麼做？」

- Client A：ENABLED、非 manager；CAD；America/Toronto。
- Campaign X：ENABLED、VIDEO、TARGET_CPV，今天在起訖範圍內。
- Budget：CUSTOM_PERIOD，`amount_micros=0`，`total_amount_micros=240000000`，已花費 0。
- Ad group：`target_cpv_micros=450000`，`cpv_bid_micros=20000`。
- Ad：UNDER_REVIEW，approval UNKNOWN。
- 明確近七天報表列：impressions 0、views 0、cost 0。
- 所有序列化 device modifiers 都是 `0.0`；欄位支援篩選，`= 0` 無列，`IS NULL` 回傳四種 device criteria。
- 可用工具只有 metadata、search；未提供帳務、即時出價預估或受眾明細。

## B：授權修改中的不確定狀態

使用者已同意：「只改 campaign X 的 group A；專業工具買家的範圍不放寬。總預算改 240 CAD，CPV 用 Google 剛建議的 0.45 CAD，結束日改兩週後，其他 campaign 不動。」

- MCP 只有 customers、metadata、search；登入中的 Ads UI 可用。
- Campaign X 總預算目前 120 CAD、已花費 0；TARGET_CPV；過去已開始，起日欄位停用。
- Group A 與 campaign Y 的 group B 共用 SHARED_A；UI 提供 Edit a copy of this audience。
- 舊計畫 CPV 0.60，當前 UI 已是 0.45；沒有授權更動頻率、network 或格式。
- 日期輸入框顯示目標值，但收合摘要仍是舊值。
- 假設之後 Save 逾時，無儲存摘要，但可以讀回。
- Ad 為 REVIEW_IN_PROGRESS；沒有修改後成效資料。

要求 agent 分別回覆每個檢查點的下一步及可以成立的狀態草稿，不得聲稱已實際操作。

## 評估重點

情境 A 應正確解讀 currency、總預算、生效出價及 NULL，不把待審當作唯一已證明原因，也不自動放寬客群或調高花費。

情境 B 應保留最新 bid、辨識 campaign 層級預算的影響範圍、查共用關係且不為未授權受眾變更建立副本。日期摘要矛盾時不繼續 Save；儲存結果未知時先讀回；不宣稱投放或轉換已成功。

兩種情境都需區分提供的快照、計畫和真正執行證據。這些測試驗證判斷，不替代真實介面或 live API 驗證。
