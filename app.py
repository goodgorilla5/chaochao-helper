import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io

st.set_page_config(page_title="燕巢-台北自動助手", layout="centered")

def process_logic(content):
    """解析 SCP 資料的核心邏輯"""
    clean_content = content.replace('+', ' ')
    elements = clean_content.split()
    final_rows = []
    current_row = []
    for item in elements:
        if item.startswith('A') and current_row:
            if "F22" in current_row:
                try:
                    cleaned = {
                        "小代": str(current_row[3])[-3:],
                        "件數": int(current_row[5].lstrip('0') or 0),
                        "公斤": int(current_row[6].lstrip('0') or 0),
                        "單價": int(current_row[7].lstrip('0')[:-1] or 0),
                        "買家": str(current_row[-1])
                    }
                    final_rows.append(cleaned)
                except: pass
            current_row = []
        if len(item) > 3 and item[0:2].isdigit() and item[2].isalpha():
            current_row.append(item[:2]); current_row.append(item[2:])
        else:
            current_row.append(item)
    return final_rows

def auto_fetch():
    """模擬真實點擊下載的函數"""
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    session = requests.Session()
    # 偽裝成一般的電腦瀏覽器
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        # 第一步：獲取網頁，拿到點擊動作必備的隱藏「門票」
        r1 = session.get(url, timeout=15)
        soup = BeautifulSoup(r1.text, 'html.parser')
        
        # 這些是點擊動作的關鍵參數
        payload = {
            '__VIEWSTATE': soup.find('input', {'name': '__VIEWSTATE'})['value'],
            '__VIEWSTATEGENERATOR': soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value'],
            '__EVENTVALIDATION': soup.find('input', {'name': '__EVENTVALIDATION'})['value'],
            'ctl00$content$lstMarket': '104', # 台北
            'ctl00$content$txtUnit': 'S00076', # 燕巢農會
            'ctl00$content$rdoFileFormat': '4', # SCP格式
            'ctl00$content$btnDownload': '下載' # 模擬點擊下載按鈕
        }
        
        # 第二步：發送點擊信號
        r2 = session.post(url, data=payload, timeout=20)
        
        if r2.status_code == 200 and "A11" in r2.text:
            return r2.text
        else:
            return None
    except Exception as e:
        return f"Error: {e}"

# --- 網頁介面 ---
st.title("🚀 燕巢-台北一鍵同步")

if st.button("🔴 點我自動抓取最新資料", use_container_width=True):
    with st.spinner("正在模擬點擊下載中..."):
        result = auto_fetch()
        if result and not str(result).startswith("Error"):
            st.session_state['data'] = result
            st.success("同步成功！")
        else:
            st.error("自動抓取失敗，可能是農委會網站阻擋了國外伺服器的模擬點擊。")

# 顯示區
if 'data' in st.session_state:
    df = pd.DataFrame(process_logic(st.session_state['data']))
    if not df.empty:
        st.divider()
        q = st.text_input("🔍 搜尋小代")
        if q: df = df[df['小代'].str.contains(q)]
        df = df.sort_values(by="單價", ascending=False)
        
        st.dataframe(df, use_container_width=True, height=500)
        st.metric("總計件數", f"{df['件數'].sum()} 件")

st.markdown("---")
st.write("如果自動抓取失敗，請參考之前的『手動下載』方案。")