import streamlit as st
import pandas as pd
import re
import requests

st.set_page_config(page_title="燕巢行情(父母專用)", layout="centered")

def process_logic(content):
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    parts = content.split('F22')
    for p in parts[1:]:
        if "S00076" in p:
            try:
                date_match = re.search(r"(\d{7,8}1)", p)
                if not date_match: continue
                date_pos = date_match.start()
                serial = p[:date_pos].strip().replace(" ", "")
                s_pos = p.find("S00076")
                level = grade_map.get(p[s_pos-2], p[s_pos-2])
                sub_id = p[s_pos+6:s_pos+9]
                nums = p.split('+')
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

# --- 自動讀取 GitHub 上的最新檔案 ---
# 這裡指向你 GitHub 倉庫中的 data.scp 檔案
RAW_URL = "https://raw.githubusercontent.com/goodgorilla5/chaochao-helper/main/today.scp"

@st.cache_data(ttl=600) # 每10分鐘檢查一次
def fetch_remote_data():
    try:
        r = requests.get(RAW_URL, timeout=5)
        if r.status_code == 200:
            return r.content.decode("big5", errors="ignore")
    except: return None
    return None

content = fetch_remote_data()

# 如果自動讀取失敗，顯示提示，並保留手動上傳備案
if not content:
    st.warning("⚠️ 雲端資料更新中，請稍後或嘗試手動上傳。")
    uploaded_file = st.file_uploader("手動上傳備案", type=['scp', 'txt'])
    if uploaded_file:
        content = uploaded_file.read().decode("big5", errors="ignore")

if content:
    data = process_logic(content)
    if data:
        df = pd.DataFrame(data)
        st.divider()
        search_query = st.text_input("🔍 輸入小代號 (例如 605)", "")
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        df = df.sort_values(by="單價", ascending=False)
        
        # 父母專用配置：欄位精簡
        st.dataframe(df[["等級", "小代", "件數", "單價", "買家"]], use_container_width=True, height=500)
        st.metric("今日 F22 總件數", f"{df['件數'].sum()} 件")