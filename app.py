import streamlit as st
import pandas as pd
import re
import requests

st.set_page_config(page_title="燕巢行情(父母專用版)", layout="centered")

# --- 解析邏輯 (保留你最完美的版本) ---
def process_logic(content):
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    # 改用更強壯的分割法，應對所有空格問題
    parts = content.split('F22')
    for p in parts[1:]:
        if "S00076" in p:
            try:
                date_match = re.search(r"(\d{7,8}1)", p)
                if not date_match: continue
                date_pos = date_match.start()
                # 流水號合併
                serial = p[:date_pos].strip().replace(" ", "")
                # 提取等級、小代
                s_pos = p.find("S00076")
                level = grade_map.get(p[s_pos-2], p[s_pos-2])
                sub_id = p[s_pos+6:s_pos+9]
                # 數字區
                nums = p.split('+')
                pieces = int(nums[0][-3:].lstrip('0') or 0)
                weight = int(nums[1].lstrip('0') or 0)
                price = int(nums[2].lstrip('0')[:-1] or 0) # 00900 -> 90
                buyer = nums[5].strip()[:4]

                final_rows.append({
                    "流水號": serial, "等級": level, "小代": sub_id,
                    "件數": pieces, "公斤": weight, "單價": price, "買家": buyer
                })
            except: continue
    return final_rows

st.title("🍎 燕巢-台北現場對帳")

# --- 核心：嘗試從 GitHub 讀取自動抓取的檔案 ---
# 注意：這裡的網址之後要換成你 GitHub 存放 SCP 的 Raw 連結
AUTO_FILE_URL = "你的GITHUB_RAW_連結" 

@st.cache_data(ttl=3600) # 每小時自動刷新一次
def load_auto_data():
    try:
        resp = requests.get(AUTO_FILE_URL, timeout=5)
        if resp.status_code == 200:
            return resp.content.decode("big5", errors="ignore")
    except:
        return None
    return None

content = load_auto_data()

# 如果自動讀取失敗，才顯示上傳按鈕 (備用)
if not content:
    uploaded_file = st.file_uploader("自動讀取失敗，請手動上傳", type=['scp', 'txt'])
    if uploaded_file:
        content = uploaded_file.read().decode("big5", errors="ignore")

if content:
    data = process_logic(content)
    if data:
        df = pd.DataFrame(data)
        
        # 父母專用：大字體顯示
        search_query = st.text_input("🔍 輸入小代號查詢 (例如 605)", "")
        
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        # 預設單價由高到低排序
        df = df.sort_values(by="單價", ascending=False)

        st.subheader("📋 今日行情明細")
        st.dataframe(df[["等級", "小代", "件數", "單價", "買家"]], use_container_width=True)
        
        st.success(f"讀取成功！當前 F22 總計: {df['件數'].sum()} 件")