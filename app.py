import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time

st.set_page_config(page_title="燕巢台北對帳-強韌版", layout="wide")

# 解析邏輯保持不變...
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

@st.cache_data(ttl=600) # 縮短快取到10分鐘，確保數據夠新
def get_latest_data():
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    # 更完整的 Header，偽裝成一般的 Chrome 瀏覽器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://amis.afa.gov.tw/"
    }
    
    session = requests.Session()
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # 1. 獲取通行證，增加 timeout 到 30 秒
            res = session.get(url, headers=headers, timeout=30)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            
            payload = {
                "__VIEWSTATE": soup.find("input", {"id": "__VIEWSTATE"})['value'],
                "__VIEWSTATEGENERATOR": soup.find("input", {"id": "__VIEWSTATEGENERATOR"})['value'],
                "__EVENTVALIDATION": soup.find("input", {"id": "__EVENTVALIDATION"})['value'],
                "ctl00$contentPlaceHolder$txtSupplyNo": "S00076 燕巢區農會",
                "ctl00$contentPlaceHolder$hfldSupplyNo": "S00076",
                "ctl00$contentPlaceHolder$btnQuery2": "4碼品名代碼" 
            }
            
            # 2. 請求數據
            post_res = session.post(url, data=payload, headers=headers, timeout=30)
            if "F22" in post_res.text:
                return parse_scp_content(post_res.text)
            else:
                return [] # 沒資料但不算錯誤
                
        except (requests.exceptions.RequestException, Exception) as e:
            if attempt < max_retries - 1:
                time.sleep(2) # 失敗後等 2 秒再試
                continue
            return f"連線農委會超時，請檢查網路或稍後再試。原因: {e}"

# --- 主程式 ---
st.title("🍎 燕巢農會 - 台北對帳自動看板")

# 提供手動刷新的按鈕（以防快取沒更新）
if st.sidebar.button("🔄 強制重新整理數據"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("🚀 正在努力穿透網路連線至農委會..."):
    data = get_latest_data()

# (後續顯示邏輯同前一版...)
if isinstance(data, list):
    if data:
        df = pd.DataFrame(data).sort_values(by="單價", ascending=False)
        # 顯示指標...
        t1, t2, t3 = st.columns(3)
        t1.metric("今日總件數", f"{df['件數'].sum()} 件")
        t2.metric("最高價", f"{df['單價'].max()} 元")
        t3.metric("總公斤", f"{df['公斤'].sum()}")
        st.divider()
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.warning("⚠️ 目前農委會尚未產出今日資料（請於中午左右查看）。")
else:
    st.error(data)