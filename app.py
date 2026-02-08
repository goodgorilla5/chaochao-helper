import streamlit as st
import pandas as pd
import re
import requests

st.set_page_config(page_title="燕巢行情對帳", layout="centered")

# --- 完美解析邏輯 ---
def process_logic(content):
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    parts = content.split('F22')
    for p in parts[1:]:
        if "S00076" in p:
            try:
                date_match = re.search(r"(\d{7,8}1)", p)
                if not date_match: continue
                serial = p[:date_match.start()].strip().replace(" ", "")
                s_pos = p.find("S00076")
                level = grade_map.get(p[s_pos-2], p[s_pos-2])
                sub_id = p[s_pos+6:s_pos+9]
                nums = p.split('+')
                pieces = int(nums[0][-3:].lstrip('0') or 0)
                price = int(nums[2].lstrip('0')[:-1] or 0)
                final_rows.append({"等級": level, "小代": sub_id, "件數": pieces, "單價": price, "流水號": serial})
            except: continue
    return final_rows

st.title("🍎 燕巢行情 (自動更新)")

# 讀取 GitHub 上的 today.scp
RAW_URL = "https://raw.githubusercontent.com/goodgorilla5/chaochao-helper/main/today.scp"

@st.cache_data(ttl=600)
def get_data():
    try:
        r = requests.get(RAW_URL, timeout=5)
        return r.text if r.status_code == 200 else None
    except: return None

content = get_data()

if content:
    data = process_logic(content)
    if data:
        df = pd.DataFrame(data)
        # 父母搜尋介面
        search = st.text_input("🔍 查詢小代號", "")
        if search: df = df[df['小代'].str.contains(search)]
        
        st.dataframe(df.sort_values("單價", ascending=False)[["等級", "小代", "件數", "單價"]], use_container_width=True)
        st.success(f"資料時間: {pd.Timestamp.now().strftime('%m/%d %H:%M')}")
else:
    st.warning("目前尚無資料，請等待早上 8:30 自動更新。")