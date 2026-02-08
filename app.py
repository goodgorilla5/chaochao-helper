import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io

# 1. 網頁基本設定
st.set_page_config(page_title="燕巢-台北市場助手", layout="centered")

# 2. 核心邏輯：解析 SCP 檔案內容
def process_logic(content):
    clean_content = content.replace('+', ' ')
    elements = clean_content.split()
    final_rows = []
    current_row = []
    
    for item in elements:
        # 遇到 A 開頭，代表新的一筆資料開始
        if item.startswith('A') and current_row:
            if "F22" in current_row:
                try:
                    cleaned = {
                        "小代": str(current_row[3])[-3:],             # 編號末三碼
                        "件數": int(current_row[5].lstrip('0') or 0), # 件數轉數字
                        "公斤": int(current_row[6].lstrip('0') or 0), # 公斤轉數字
                        "單價": int(current_row[7].lstrip('0')[:-1] or 0), # 單價去尾轉數字
                        "買家": str(current_row[-1])                  # 買家代號
                    }
                    final_rows.append(cleaned)
                except: pass
            current_row = []
        
        # 拆分 11S / 21A 等格式
        if len(item) > 3 and item[0:2].isdigit() and item[2].isalpha():
            current_row.append(item[:2])
            current_row.append(item[2:])
        else:
            current_row.append(item)
    return final_rows

# 3. 自動抓取邏輯：模擬手機去農委會下載
def fetch_amis_data():
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
        'Referer': url
    }
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 第一步：獲取隱藏驗證碼
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        viewstate = soup.find('input', {'id': '__VIEWSTATE'})['value']
        gen = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value']
        validation = soup.find('input', {'id': '__EVENTVALIDATION'})['value']
        
        # 第二步：發送下載指令
        payload = {
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': gen,
            '__EVENTVALIDATION': validation,
            'ctl00$content$lstMarket': '104',     # 台北市場
            'ctl00$content$txtUnit': 'S00076',     # 燕巢區農會
            'ctl00$content$rdoFileFormat': '4',    # SCP格式
            'ctl00$content$btnDownload': '下載'
        }
        
        res = session.post(url, data=payload, timeout=15)
        if res.status_code == 200 and len(res.content) > 100:
            return res.content.decode('utf-8', errors='ignore')
        else:
            return None
    except:
        return None

# --- 4. 網頁介面顯示 ---
st.title("🍎 燕巢-台北現場助手")
st.caption("自動抓取農委會 S00076 台北市場 F22 資料")

# 功能按鈕
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🔄 一鍵自動更新"):
        with st.spinner("抓取中..."):
            content = fetch_amis_data()
            if content:
                st.session_state['scp_content'] = content
                st.success("更新成功！")
            else:
                st.error("目前抓不到資料，請改用手動上傳。")

# 手動上傳 (預留備用)
with st.expander("手動上傳 SCP 檔案"):
    uploaded_file = st.file_uploader("選擇檔案", type=['scp', 'txt'])
    if uploaded_file:
        st.session_state['scp_content'] = uploaded_file.read().decode("utf-8", errors="ignore")

# 顯示資料表格
if 'scp_content' in st.session_state:
    data = process_logic(st.session_state['scp_content'])
    if data:
        df = pd.DataFrame(data)
        
        st.divider()
        # 搜尋與排序功能
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            q = st.text_input("🔍 搜尋小代", placeholder="輸入數字")
        with s_col2:
            sort_opt = st.selectbox("單價排序", ["高 → 低", "低 → 高"])

        # 過濾與排序
        if q:
            df = df[df['小代'].str.contains(q)]
        df = df.sort_values(by="單價", ascending=(sort_opt == "低 → 高"))

        # 表格呈現
        st.dataframe(df, use_container_width=True, height=450)
        
        # 底部統計
        st.metric("當前畫面總件數", f"{df['件數'].sum()} 件")
    else:
        st.warning("檔案中找不到 F22 的資料。")

st.markdown("---")
st.info("💡 提示：若自動更新卡住，通常是政府網站擋掉連線，請手動下載後上傳。")