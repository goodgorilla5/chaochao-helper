import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io

# 設定網頁標題
st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

def process_logic(content):
    """解析 SCP 內容的極簡邏輯"""
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

def fetch_amis_data():
    """自動連線農委會下載 SCP 檔案"""
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    session = requests.Session()
    
    try:
        # 1. 取得初始頁面以獲取隱藏參數 (ViewState)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        viewstate = soup.find('input', {'id': '__VIEWSTATE'})['value']
        validation = soup.find('input', {'id': '__EVENTVALIDATION'})['value']
        
        # 2. 模擬點擊下載按鈕的參數
        payload = {
            '__VIEWSTATE': viewstate,
            '__EVENTVALIDATION': validation,
            'ctl00$content$lstMarket': '104', # 台北市場
            'ctl00$content$txtUnit': 'S00076', # 燕巢區農會
            'ctl00$content$rdoFileFormat': '4', # 4碼品名代碼 (SCP)
            'ctl00$content$btnDownload': '下載'
        }
        
        res = session.post(url, data=payload)
        if res.status_code == 200 and len(res.content) > 100:
            return res.content.decode('utf-8', errors='ignore')
        else:
            return None
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

# --- 網頁介面 ---
st.title("🍎 燕巢-台北自動對帳系統")

# 自動抓取按鈕
if st.button("🔄 一鍵同步今日台北資料"):
    with st.spinner("正在連線農委會抓取最新 SCP..."):
        content = fetch_amis_data()
        if content:
            st.session_state['data_content'] = content
            st.success("資料更新成功！")
        else:
            st.error("目前網站可能無資料或連線受阻。")

# 也可以手動上傳 (備用)
uploaded_file = st.file_uploader("或手動上傳 SCP", type=['scp', 'txt'])
if uploaded_file:
    st.session_state['data_content'] = uploaded_file.read().decode("utf-8", errors="ignore")

# 顯示資料
if 'data_content' in st.session_state:
    data = process_logic(st.session_state['data_content'])
    if data:
        df = pd.DataFrame(data)
        
        st.divider()
        # 搜尋與排序
        col1, col2 = st.columns(2)
        with col1:
            search = st.text_input("🔍 搜尋小代", placeholder="例如: 019")
        with col2:
            sort = st.selectbox("排序單價", ["由高至低", "由低至高"])
            
        if search:
            df = df[df['小代'].str.contains(search)]
        
        df = df.sort_values(by="單價", ascending=(sort == "由低至高"))
        
        # 顯示大字體表格
        st.subheader("📋 交易資料預覽")
        st.dataframe(df, use_container_width=True, height=500)
        
        # 統計資訊
        st.metric("總件數", f"{df['件數'].sum()} 件")
    else:
        st.warning("檔案解析成功，但找不到 F22 資料。")