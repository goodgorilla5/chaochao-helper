import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="燕巢自動對帳助手", layout="centered")

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

def final_attempt_fetch():
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        res1 = session.get(url, timeout=15)
        soup = BeautifulSoup(res1.text, 'html.parser')
        payload = {
            '__VIEWSTATE': soup.find('input', {'id': '__VIEWSTATE'})['value'],
            '__VIEWSTATEGENERATOR': soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value'],
            '__EVENTVALIDATION': soup.find('input', {'id': '__EVENTVALIDATION'})['value'],
            'ctl00$contentPlaceHolder$txtSupplyNo': 'S00076 燕巢區農會',
            'ctl00$contentPlaceHolder$hfldSupplyNo': 'S00076',
            'ctl00$contentPlaceHolder$btnQuery2': '下載(4碼品名代碼)'
        }
        res2 = session.post(url, data=payload, timeout=25)
        if res2.status_code == 200 and "A11" in res2.text:
            return res2.text
        return None
    except:
        return None

st.title("🍎 燕巢-台北全自動助手")

if st.button("🔴 執行全自動抓取", use_container_width=True):
    with st.spinner("正在根據新 ID 突破中..."):
        data = final_attempt_fetch()
        if data:
            st.session_state['data'] = data
            st.success("🎉 自動抓取成功！")
        else:
            st.error("自動抓取仍受阻。請用下方的『書籤法』。")

uploaded_file = st.file_uploader("📂 手動上傳 (備用)", type=['scp', 'txt'])
if uploaded_file:
    st.session_state['data'] = uploaded_file.read().decode("utf-8", errors="ignore")

if 'data' in st.session_state:
    df = pd.DataFrame(process_logic(st.session_state['data']))
    if not df.empty:
        q = st.text_input("🔍 搜尋小代")
        if q: df = df[df['小代'].str.contains(q)]
        df = df.sort_values(by="單價", ascending=False)
        st.dataframe(df, use_container_width=True, height=400)
        st.metric("總計件數", f"{df['件數'].sum()} 件")