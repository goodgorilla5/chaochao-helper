import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="燕巢台北終極助手", layout="centered")

def parse_scp(content):
    rows = []
    for line in content.split('\n'):
        if "F22" in line:
            p = line.replace('+', ' ').split()
            try:
                rows.append({"小代": str(p[3])[-3:], "件數": int(p[5].lstrip('0') or 0), "單價": int(p[7].lstrip('0')[:-1] or 0), "買家": p[-1]})
            except: continue
    return rows

def fetch_data():
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Origin': 'https://amis.afa.gov.tw',
        'Referer': url,
    }
    s = requests.Session()
    try:
        r1 = s.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r1.text, 'html.parser')
        data = {
            '__VIEWSTATE': soup.find('input', {'id': '__VIEWSTATE'})['value'],
            '__VIEWSTATEGENERATOR': soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value'],
            '__EVENTVALIDATION': soup.find('input', {'id': '__EVENTVALIDATION'})['value'],
            'ctl00$contentPlaceHolder$txtSupplyNo': 'S00076 燕巢區農會',
            'ctl00$contentPlaceHolder$hfldSupplyNo': 'S00076',
            'ctl00$contentPlaceHolder$btnQuery2': '下載(4碼品名代碼)'
        }
        time.sleep(1) # 模擬真人思考時間
        r2 = s.post(url, data=data, headers=headers, timeout=15)
        if "A11" in r2.text: return r2.text
        return None
    except: return None

st.title("🍎 燕巢-台北懶人自動化測試")

if st.button("🚀 嘗試全自動抓取 (挑戰防火牆)"):
    with st.spinner("正在偽裝成手機連線中..."):
        res = fetch_data()
        if res:
            st.session_state['data'] = res
            st.success("🎉 竟然成功了！這代表今天防火牆沒抓你！")
        else:
            st.error("❌ 還是被擋住了。這不是程式的問題，是「地理 IP」的問題。")

uploaded_file = st.file_uploader("📂 手動上傳 (保險方案)", type=['scp', 'txt'])
if uploaded_file:
    st.session_state['data'] = uploaded_file.read().decode("utf-8", errors="ignore")

if 'data' in st.session_state:
    df = pd.DataFrame(parse_scp(st.session_state['data']))
    if not df.empty:
        q = st.text_input("🔍 搜小代")
        df = df[df['小代'].str.contains(q)] if q else df
        st.dataframe(df.sort_values("單價", ascending=False), use_container_width=True)
        st.metric("總件數", f"{df['件數'].sum()} 件")