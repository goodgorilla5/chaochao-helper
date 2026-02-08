# AMIS 農產品行情下載工具

這是一個針對「農產品批發市場交易行情站」開發的自動化下載腳本。

## 🛠 如何使用
1. 安裝套件：`pip install -r requirements.txt`
2. 獲取 ViewState：
   - 在瀏覽器開啟查詢頁面，填好日期與代號。
   - 按下 `F12` 開啟開發者工具，切換到 `Network` 標籤。
   - 點擊網頁上的「下載」按鈕。
   - 找到那個 `POST` 請求，複製 `Payload` 裡的 `__VIEWSTATE` 與 `__EVENTVALIDATION`。
3. 將參數填入 `scraper.py` 並執行：`python scraper.py`

## ⚠️ 注意事項
- `__VIEWSTATE` 具備時效性，若發生錯誤請重新獲取。
- 本工具僅供學術與資料分析使用。