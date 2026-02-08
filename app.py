import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="燕巢-台北深度助手", layout="centered")

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
            current_row.append(item[:2]); current_row.append(item[2:])
        else:
            current_row.append(item)
    return final_rows

def deep_fetch():
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': url
    })
    
    try:
        # 第一步：進入頁面拿到門票
        res1 = session.get(url, timeout=15)
        soup = BeautifulSoup(res1.text, 'html.parser')
        
        # 準備模擬點擊參數
        # 注意：__EVENTTARGET 設為 btnDownload，直接跳過選單選取的動態限制
        payload = {
            '__VIEWSTATE': soup.find('input', {'name': '__VIEWSTATE'})['value'],
            '__VIEWSTATEGENERATOR': soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value'],
            '__EVENTVALIDATION': soup.find('input', {'name': '__EVENTVALIDATION'})['value'],
            'ctl00$content$lstMarket': '104',              # 台北
            'ctl00$content$txtUnit': 'S00076',             # 直接填入代號 (嘗試繞過點擊選單)
            'ctl00$content$rdoFileFormat': '4',            # SCP 格式
            'ctl00$content$btnDownload': '下載(4碼品名代碼)'  # 模擬按下那個按鈕
        }
        
        # 第二步：直接發送下載請求
        res2 = session.post(url, data=payload, timeout=25)
        
        if res2.status_code == 200 and "A11" in res2.text:
            return res2.text
        else:
            return None
    except Exception as e:
        return None

# --- UI 介面 ---
st.title("🍎 燕巢-台北深度同步")
st.write("這會嘗試繞過網頁限制，直接點擊下載按鈕。")

if st.button("🚀 執行深度抓取", use_container_width=True):
    with st.spinner("模擬人工點擊中..."):
        data_text = deep_fetch()
        if data_text:
            st.session_state['current_data'] = data_text
            st.success("同步成功！")
        else:
            st.error("自動抓取受阻。原因：該網頁選單需要滑鼠實體點擊觸發 JS 腳本。")

if 'current_data' in st.session_state:
    results = process_logic(st.session_state['current_data'])
    if results:
        df = pd.DataFrame(results)
        st.divider()
        q = st.text_input("🔍 搜尋小代")
        if q: df = df[df['小代'].str.contains(q)]
        df = df.sort_values(by="單價", ascending=False)
        st.dataframe(df, use_container_width=True, height=500)
        st.metric("總計件數", f"{df['件數'].sum()} 件")

st.markdown("---")
st.caption("註：若持續失敗，建議使用我之前提供的『JavaScript 1秒下載書籤』，那是目前最強的破解法。")