import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

# --- 新增：自動抓取功能 ---
def fetch_amis_data():
    # 1. 計算民國日期 (如 1150208)
    now = datetime.now()
    roc_date = f"{now.year - 1911}{now.strftime('%m%d')}"
    
    url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        session = requests.Session()
        # 第一步：獲取隱藏的 ViewState
        resp = session.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        viewstate = soup.find('input', attrs={'name': '__VIEWSTATE'})['value']
        event_validation = soup.find('input', attrs={'name': '__EVENTVALIDATION'})['value']
        
        # 第二步：模擬點擊下載 (這裡的參數是根據你的框架檔案推算的)
        payload = {
            "__VIEWSTATE": viewstate,
            "__EVENTVALIDATION": event_validation,
            "txtKeyWord": "S00076", # 燕巢區農會
            "btnQuery": "查詢",      # 模擬點擊查詢
            "txtDate": roc_date     # 自動填入今日日期
        }
        
        # 注意：實際下載可能需要根據點擊按鈕的 ID 調整 payload
        # 這裡假設點擊後直接回傳 SCP 內容
        response = session.post(url, data=payload, headers=headers)
        
        if response.status_code == 200 and len(response.content) > 100:
            return response.content.decode("big5", errors="ignore")
        else:
            return None
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

# --- 原有的解析邏輯 (保留你最完美的版本) ---
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
                    serial = line[:date_pos].strip().replace(" ", "")
                    remaining = line[date_pos:]
                    s_pos = remaining.find("S00076")
                    raw_turn = remaining[s_pos-2]
                    level = grade_map.get(raw_turn, raw_turn)
                    sub_id = remaining[s_pos+6:s_pos+9]
                    nums = line.split('+')
                    pieces = int(nums[0][-3:].lstrip('0') or 0)
                    weight = int(nums[1].lstrip('0') or 0)
                    price_raw = nums[2].lstrip('0')
                    price = int(price_raw[:-1] if price_raw else 0)
                    buyer = nums[5].strip()[:4]

                    final_rows.append({
                        "流水號": serial, "等級": level, "小代": sub_id,
                        "件數": pieces, "公斤": weight, "單價": price, "買家": buyer
                    })
            except: continue
    return final_rows

st.title("🍎 燕巢-台北現場對帳")

# --- 側邊欄控制 ---
with st.sidebar:
    st.header("數據更新")
    auto_data = None
    if st.button("🔄 同步今日最新資料"):
        with st.spinner("正在連線至 AMIS..."):
            auto_data = fetch_amis_data()
            if auto_data:
                st.success("抓取成功！")
            else:
                st.error("抓取失敗，請改用手動上傳。")

uploaded_file = st.file_uploader("或手動上傳 SCP 檔案", type=['scp', 'txt', 'SCP'])

# 優先讀取自動抓取的資料，沒有的話再看手動上傳
content = None
if auto_data:
    content = auto_data
elif uploaded_file:
    try:
        content = uploaded_file.read().decode("big5", errors="ignore")
    except:
        content = uploaded_file.read().decode("utf-8", errors="ignore")

if content:
    data = process_logic(content)
    if data:
        df = pd.DataFrame(data)
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1: search_query = st.text_input("🔍 搜尋小代")
        with col2: sort_order = st.selectbox("排序單價", ["由高至低", "由低至高"])
        with col3: show_serial = st.checkbox("顯示流水號", value=False)

        if search_query: df = df[df['小代'].str.contains(search_query)]
        df = df.sort_values(by="單價", ascending=(sort_order == "由低至高"))

        display_columns = ["等級", "小代", "件數", "公斤", "單價", "買家"]
        if show_serial: display_columns.insert(0, "流水號")

        st.dataframe(df[display_columns], use_container_width=True, height=500,
                    column_config={"流水號": st.column_config.TextColumn("流水號", width="small")})
        st.metric("當前 F22 總件數", f"{df['件數'].sum()} 件")