import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime

st.set_page_config(page_title="燕巢台北對帳-自動導航版", layout="wide")

# 解析 SCP 內容
def parse_scp_content(content):
    final_rows = []
    lines = content.split('\n')
    for line in lines:
        if "F22" in line:
            parts = line.replace('+', ' ').split()
            try:
                final_rows.append({
                    "小代": str(parts[3])[-3:],
                    "件數": int(parts[5].lstrip('0') or 0),
                    "公斤": int(parts[6].lstrip('0') or 0),
                    "單價": int(parts[7].lstrip('0')[:-1] or 0),
                    "買家": parts[-1]
                })
            except: continue
    return final_rows

# 核心功能：直接從網頁抓取數據
@st.cache_data(ttl=3600)  # 快取功能：一小時內重複打開網頁，不需要重新抓取，讀取超快
def get_latest_data():
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    session = requests.Session()
    try:
        # 1. 獲取通行證
        res = session.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 2. 準備 PostBack 參數
        payload = {
            "__VIEWSTATE": soup.find("input", {"id": "__VIEWSTATE"})['value'],
            "__VIEWSTATEGENERATOR": soup.find("input", {"id": "__VIEWSTATEGENERATOR"})['value'],
            "__EVENTVALIDATION": soup.find("input", {"id": "__EVENTVALIDATION"})['value'],
            "ctl00$contentPlaceHolder$txtSupplyNo": "S00076 燕巢區農會",
            "ctl00$contentPlaceHolder$hfldSupplyNo": "S00076",
            "ctl00$contentPlaceHolder$btnQuery2": "4碼品名代碼" 
        }
        
        # 3. 請求數據
        post_res = session.post(url, data=payload, headers=headers, timeout=15)
        return parse_scp_content(post_res.text)
    except Exception as e:
        return f"錯誤: {e}"

# --- 主程式執行區 ---
st.title("🍎 燕巢農會 - 台北對帳自動看板")

# 這裡就是關鍵：一進網頁直接執行抓取
with st.spinner("🚀 正在自動連線農委會獲取最新數據..."):
    data = get_latest_data()

if isinstance(data, list) and data:
    df = pd.DataFrame(data)
    
    # 搜尋功能 (這還是要留著，方便你找特定小代)
    search = st.sidebar.text_input("🔍 搜尋小代後3碼", placeholder="例如: 025")
    if search:
        df = df[df['小代'].str.contains(search)]
    
    # 排序：單價最高排前面
    df = df.sort_values(by="單價", ascending=False)

    # 顯示數據
    t1, t2, t3 = st.columns(3)
    t1.metric("今日總件數", f"{df['件數'].sum()} 件")
    t2.metric("台北最高價", f"{df['單價'].max()} 元")
    t3.metric("總公斤數", f"{df['公斤'].sum()} kg")

    st.divider()
    st.dataframe(df, use_container_width=True, height=700)
    
    st.caption(f"📅 資料更新時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.sidebar.info("資料每小時自動刷新一次，若需強制更新請重新整理網頁。")

elif isinstance(data, list) and not data:
    st.warning("⚠️ 目前農委會網站尚未產生今日的交易檔案 (通常在中午前更新)。")
else:
    st.error(f"❌ 系統連線異常：{data}")