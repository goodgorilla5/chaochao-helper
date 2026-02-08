import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 核心邏輯：模擬 PostBack 下載 ---
def auto_fetch_amis():
    now = datetime.now()
    roc_date = f"{now.year - 1911}{now.strftime('%m%d')}"
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": url
    }

    try:
        session = requests.Session()
        # 1. 第一次造訪拿 ViewState
        res1 = session.get(url, headers=headers)
        soup = BeautifulSoup(res1.text, 'html.parser')
        
        # 提取隱藏欄位
        vs = soup.find('input', id='__VIEWSTATE')['value']
        ev = soup.find('input', id='__EVENTVALIDATION')['value']
        vg = soup.find('input', id='__VIEWSTATEGENERATOR')['value']

        # 2. 模擬「選擇農會」並「點擊下載」的動作
        # 這裡就是破解 Javascript DoPostBack 的關鍵 Payload
        payload = {
            "__EVENTTARGET": "ctl00$contentPlaceHolder$lbtnDownload", # 這是你找出的關鍵 ID
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": vs,
            "__VIEWSTATEGENERATOR": vg,
            "__EVENTVALIDATION": ev,
            "ctl00$contentPlaceHolder$txtKeyWord": "S00076", # 燕巢區農會
            "ctl00$contentPlaceHolder$txtDate": roc_date,    # 自動帶入當天日期
            "ctl00$contentPlaceHolder$rbtnList": "1"         # 假設下載格式是 1
        }

        # 3. 送出 POST 請求拿回檔案
        res2 = session.post(url, data=payload, headers=headers)
        
        if res2.status_code == 200 and len(res2.content) > 500:
            return res2.content.decode("big5", errors="ignore")
        else:
            st.error("伺服器拒絕抓取，可能需要手動選擇一次。")
            return None
    except Exception as e:
        st.error(f"連線異常: {e}")
        return None

# --- 原本完美的解析邏輯 (保留等級轉換、流水號合併) ---
# ... (此處省略 process_logic 代碼，維持你之前的完美版本) ...

st.title("🍎 燕巢-台北現場對帳")

# --- 自動同步按鈕 ---
with st.sidebar:
    st.header("⚙️ 雲端同步")
    if st.button("🚀 抓取今日最新 F22"):
        with st.spinner("正在滲透 AMIS 系統..."):
            fetched_content = auto_fetch_amis()
            if fetched_content:
                st.session_state['scp_content'] = fetched_content
                st.success("同步成功！")

# 手動上傳當作備案
uploaded_file = st.file_uploader("📂 或者手動上傳檔案", type=['scp', 'txt', 'SCP'])
if uploaded_file:
    st.session_state['scp_content'] = uploaded_file.read().decode("big5", errors="ignore")

# 讀取資料
if 'scp_content' in st.session_state:
    data = process_logic(st.session_state['scp_content'])
    # ... (顯示資料、搜尋、等級排序、顯示流水號等邏輯) ...