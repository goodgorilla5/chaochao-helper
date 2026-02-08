import requests
import os

class AmisDownloader:
    def __init__(self):
        self.url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Origin': 'https://amis.afa.gov.tw',
            'Referer': self.url
        }

    def download_report(self, date_str, supply_no, viewstate, validation):
        """
        執行 POST 請求下載資料
        :param date_str: 民國日期格式 (如 115/02/08)
        :param supply_no: 供應商編號 (如 A00013)
        """
        payload = {
            '__EVENTTARGET': 'ctl00$contentPlaceHolder$lbtnDownload',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': '4F2132E6',
            '__EVENTVALIDATION': validation,
            'ctl00$contentPlaceHolder$txtStartDate': date_str,
            'ctl00$contentPlaceHolder$txtEndDate': date_str,
            'ctl00$contentPlaceHolder$txtSupplyNo': f'{supply_no} 台北市農會',
            'ctl00$contentPlaceHolder$hfldSupplyNo': supply_no
        }

        print(f"🚀 啟動任務：下載 {date_str} 資料...")
        
        try:
            response = requests.post(self.url, data=payload, headers=self.headers)
            if response.status_code == 200:
                filename = f"report_{date_str.replace('/', '')}.txt"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ 下載成功！存檔為: {filename}")
            else:
                print(f"❌ 下載失敗，狀態碼: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 發生錯誤: {e}")

if __name__ == "__main__":
    # 這裡填入你剛才在 Chrome 抓到的那串長密碼
    VS = "你提供的__VIEWSTATE內容"
    VAL = "你提供的__EVENTVALIDATION內容"
    
    bot = AmisDownloader()
    bot.download_report('115/02/08', 'A00013', VS, VAL)