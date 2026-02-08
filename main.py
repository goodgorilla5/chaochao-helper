import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

class AmisAutoBot:
    def __init__(self):
        self.url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
        self.session = requests.Session() # 使用 Session 維持 Cookie
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }

    def get_params(self):
        """ 第一步：先拿隱藏參數 """
        r = self.session.get(self.url, headers=self.headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        vs = soup.find('input', {'id': '__VIEWSTATE'})['value']
        gen = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value']
        val = soup.find('input', {'id': '__EVENTVALIDATION'})['value']
        return vs, gen, val

    def run(self):
        vs, gen, val = self.get_params()
        
        # 設定日期 (範例：抓今天)
        date_str = "115/02/08" # 這裡可以用 datetime 模組自動生成
        
        payload = {
            '__EVENTTARGET': 'ctl00$contentPlaceHolder$lbtnDownload',
            '__VIEWSTATE': vs,
            '__VIEWSTATEGENERATOR': gen,
            '__EVENTVALIDATION': val,
            'ctl00$contentPlaceHolder$txtStartDate': date_str,
            'ctl00$contentPlaceHolder$txtEndDate': date_str,
            'ctl00$contentPlaceHolder$txtSupplyNo': 'A00013 台北市農會',
            'ctl00$contentPlaceHolder$hfldSupplyNo': 'A00013'
        }

        print(f"正在下載 {date_str} 的資料...")
        resp = self.session.post(self.url, data=payload, headers=self.headers)
        
        if resp.status_code == 200:
            with open(f"data_{date_str.replace('/','')}.txt", "wb") as f:
                f.write(resp.content)
            print("下載成功！")
        else:
            print("下載失敗。")

if __name__ == "__main__":
    AmisAutoBot().run()