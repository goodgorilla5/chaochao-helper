import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

# --- 核心：根據書籤啟發的自動抓取邏輯 ---
def auto_fetch_amis():
    now = datetime.now()
    # 民國日期格式 (例如 1150208)
    roc_date = f"{now.year - 1911}{now.strftime('%m%d')}"
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": url
    }

    try:
        session = requests.Session()
        # 1. 抓取網頁初始狀態與 ViewState
        res1 = session.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res1.text, 'html.parser')
        
        vs = soup.find('input', id='__VIEWSTATE')['value']
        ev = soup.find('input', id='__EVENTVALIDATION')['value']
        vg = soup.find('input', id='__VIEWSTATEGENERATOR')['value']

        # 2. 模擬書籤邏輯：帶入 S00076 並觸發 btnQuery2
        payload = {
            "__EVENTTARGET": "ctl00$contentPlaceHolder$btnQuery2",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": vs,
            "__VIEWSTATEGENERATOR": vg,
            "__EVENTVALIDATION": ev,
            "ctl00$contentPlaceHolder$txtKeyWord": "S00076",
            "ctl00$contentPlaceHolder$hfldSupplyNo": "S00076", # 這是書籤成功的關鍵！
            "ctl00$contentPlaceHolder$txtDate": roc_date,
            "ctl00$contentPlaceHolder$rbtnList": "1"
        }

        # 3. 發送請求
        res2 = session.post(url, data=payload, headers=headers, timeout=15)
        
        if res2.status_code == 200 and "S00076" in res2.text:
            return res2.text
        else:
            return None
    except Exception as e:
        st.sidebar.error(f"同步失敗: {str(e)}")
        return None

# --- 解析邏輯 (流水號合併、特優良等級) ---
def process_logic(content):
    raw_lines = content.split('    ')
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    for line in raw_lines:
        if "F22" in line and "S00076" in line:
            try:
                date_match = re.search(r"(\d{7,8}1)\s+\d{2}S00076", line)
                if date_match:
                    date_pos = date_match.start()
                    serial = line[:date_pos].strip().replace(" ", "") # 合併流水號
                    remaining = line[date_pos:]
                    s_pos = remaining.find("S00076")
                    raw_turn = remaining[s_pos-2]
                    level = grade_map.get(raw_turn, raw_turn) # 等級轉換
                    sub_id = remaining[s_pos+6:s_pos+9]
                    nums = line.split('+')
                    pieces = int(nums[0][-3:].lstrip('0') or 0)
                    weight = int(nums[1].lstrip('0') or 0)
                    price_raw = nums[2].lstrip('0')
                    price = int(price_raw[:-1] if price_raw else 0) # 1250 -> 125
                    buyer = nums[5].strip()[:4]
                    final_rows.append({
                        "流水號": serial, "等級": level, "小代": sub_id,
                        "件數": pieces, "公斤": weight, "單價": price, "買家": buyer
                    })
            except: continue
    return final_rows

st.title("🍎 燕巢-台北現場對帳")

# --- 側邊欄：自動化按鈕 ---
with st.sidebar:
    st.header("⚙️ 數據同步")
    if st.button("🚀 執行雲端同步 (今日 F22)"):
        with st.spinner("正在嘗試連線 AMIS..."):
            fetched = auto_fetch_amis()
            if fetched:
                st.session_state['main_content'] = fetched
                st.success("同步成功！")
            else:
                st.error("自動抓取失敗，請改用書籤下載後手動上傳。")

# --- 主畫面：上傳與顯示 ---
uploaded_file = st.file_uploader("📂 上傳 SCP 檔案 (自動同步失敗時使用)", type=['scp', 'txt', 'SCP'])

# 優先順序：自動抓取的資料 > 手動上傳的資料
final_content = None
if 'main_content' in st.session_state:
    final_content = st.session_state['main_content']
if uploaded_file:
    try:
        final_content = uploaded_file.read().decode("big5", errors="ignore")
    except:
        final_content = uploaded_file.read().decode("utf-8", errors="ignore")

if final_content:
    data = process_logic(final_content)
    if data:
        df = pd.DataFrame(data)
        st.divider()
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: search_query = st.text_input("🔍 搜尋小代")
        with c2: sort_order = st.selectbox("排序單價", ["由高至低", "由低至高"])
        with c3: show_serial = st.checkbox("顯示流水號", value=False)

        if search_query: df = df[df['小代'].str.contains(search_query)]
        df = df.sort_values(by="單價", ascending=(sort_order == "由低至高"))

        display_cols = ["等級", "小代", "件數", "公斤", "單價", "買家"]
        if show_serial: display_cols.insert(0, "流水號")

        st.dataframe(df[display_cols], use_container_width=True, height=500)
        st.metric("當前 F22 總件數", f"{df['件數'].sum()} 件")