import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io
import time

# 1. 網頁基本設定（優化手機大字體）
st.set_page_config(page_title="燕巢-台北現場助手", layout="centered")

# 2. 核心解析邏輯
def process_logic(content):
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
            current_row.append(item[:2])
            current_row.append(item[2:])
        else:
            current_row.append(item)
    return final_rows

# 3. 強化版自動抓取邏輯
def fetch_amis_data():
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': url
    }
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 第一步：獲取隱藏參數
        response = session.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        viewstate = soup.find('input', {'id': '__VIEWSTATE'})['value']
        gen = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value']
        validation = soup.find('input', {'id': '__EVENTVALIDATION'})['value']
        
        # 第二步：模擬下載請求
        payload = {
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': gen,
            '__EVENTVALIDATION': validation,
            'ctl00$content$lstMarket': '104',     # 台北市場
            'ctl00$content$txtUnit': 'S00076',     # 燕巢區農會
            'ctl00$content$rdoFileFormat': '4',    # SCP格式
            'ctl00$content$btnDownload': '下載'
        }
        
        time.sleep(1) # 稍微等待模擬真人
        res = session.post(url, data=payload, timeout=20)
        
        # 檢查是否抓到 SCP 特徵 (以 A11 開頭的字串)
        if res.status_code == 200 and "A11" in res.text:
            return res.text
        else:
            return None
    except:
        return None

# --- 4. 網頁介面 ---
st.title("🍎 燕巢-台北對帳助手")
st.info("💡 說明：點擊按鈕自動抓取。若失敗，請點下方『手動上傳』。")

# 功能按鈕區
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🔄 一鍵自動同步"):
        with st.spinner("連線農委會中..."):
            content = fetch_amis_data()
            if content:
                st.session_state['scp_content'] = content
                st.success("同步成功！")
            else:
                st.error("自動抓取受阻（可能今日無資料或被網站攔截）。")

# 手動上傳區
with st.expander("📂 手動上傳（備用）"):
    uploaded_file = st.file_uploader("選擇您下載的 SCP 檔案", type=['scp', 'txt'])
    if uploaded_file:
        st.session_state['scp_content'] = uploaded_file.read().decode("utf-8", errors="ignore")

# 顯示資料
if 'scp_content' in st.session_state:
    data = process_logic(st.session_state['scp_content'])
    if data:
        df = pd.DataFrame(data)
        
        st.divider()
        # 功能：搜尋與排序
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            q = st.text_input("🔍 搜尋小代", placeholder="輸入後三碼")
        with s_col2:
            sort_opt = st.selectbox("單價排序", ["高至低", "低至高"])

        if q:
            df = df[df['小代'].str.contains(q)]
        df = df.sort_values(by="單價", ascending=(sort_opt == "低至高"))

        # 大表格顯示
        st.dataframe(df, use_container_width=True, height=500)
        
        # 大字體統計
        st.metric("當前總件數", f"{df['件數'].sum()} 件")
    else:
        st.warning("檔案內找不到 F22 資料。")

st.markdown("---")
st.caption("燕巢農會台北市場專用工具")