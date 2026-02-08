import streamlit as st
import pandas as pd
import re
import requests
import time

st.set_page_config(page_title="燕巢行情對帳", layout="centered")

# --- 強化版解析邏輯：改用「加號與特徵定位」防止資料偏移 ---
def process_logic(content):
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    
    # 不再依賴空格數量，直接用 F22 作為每一筆交易的起點
    parts = content.split('F22')
    for p in parts[1:]:
        if "S00076" in p:
            try:
                # 1. 抓取流水號：找日期(1150xxx1)之前的數字並合併
                date_match = re.search(r"(\d{7,8}1)", p)
                if not date_match: continue
                date_pos = date_match.start()
                serial = p[:date_pos].strip().replace(" ", "")
                
                # 2. 抓取等級與小代：以 S00076 為中心定位
                s_pos = p.find("S00076")
                level_code = p[s_pos-2] # S00076 前兩格是等級代碼
                level = grade_map.get(level_code, level_code)
                sub_id = p[s_pos+6:s_pos+9] # S00076 後三碼是小代
                
                # 3. 抓取件數、公斤、單價：利用 + 號分割最準確
                nums = p.split('+')
                # 數字清洗：只留數字，避免抓到雜質
                pieces = int(re.sub(r"\D", "", nums[0])[-3:] or 0)
                weight = int(re.sub(r"\D", "", nums[1]) or 0)
                
                # 單價修正：去掉最後一個 0 (例如 00900 -> 90)
                price_raw = re.sub(r"\D", "", nums[2])
                price = int(price_raw[:-1] if price_raw else 0)
                
                # 4. 買家：最後一個 + 號後面的前四位
                buyer = nums[5].strip()[:4]

                final_rows.append({
                    "流水號": serial, "等級": level, "小代": sub_id, 
                    "件數": pieces, "公斤": weight, "單價": price, "買家": buyer
                })
            except: continue
    return final_rows

st.title("🍎 燕巢-台北現場對帳")

# --- 讀取 GitHub 今日資料 (強制刷新) ---
timestamp = int(time.time())
RAW_URL = f"https://raw.githubusercontent.com/goodgorilla5/chaochao-helper/main/today.scp?t={timestamp}"

@st.cache_data(ttl=60)
def fetch_auto_data(url):
    try:
        r = requests.get(url, timeout=10, headers={'Cache-Control': 'no-cache'})
        if r.status_code == 200:
            return r.content.decode("big5", errors="ignore")
    except: return None
    return None

auto_content = fetch_auto_data(RAW_URL)
final_content = None

# --- 介面邏輯 ---
if auto_content and len(auto_content) > 100:
    st.success("✅ 已自動載入今日雲端資料")
    with st.expander("手動上傳備援"):
        manual_file = st.file_uploader("若雲端資料不對，請上傳 SCP", type=['scp', 'txt'])
        if manual_file:
            final_content = manual_file.read().decode("big5", errors="ignore")
    if not final_content:
        final_content = auto_content
else:
    st.warning("⚠️ 雲端目前無資料，請點擊下方手動上傳。")
    manual_file = st.file_uploader("📂 手動上傳 SCP 檔案", type=['scp', 'txt'])
    if manual_file:
        final_content = manual_file.read().decode("big5", errors="ignore")

# --- 顯示區 ---
if final_content:
    data = process_logic(final_content)
    if data:
        df = pd.DataFrame(data)
        st.divider()
        
        # 搜尋功能
        search_query = st.text_input("🔍 搜尋小代 (例如: 605)", "")
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        # 【修正】1. 強制預設由單價高至低排序
        df = df.sort_values(by="單價", ascending=False)
        
        # 【修正】2. 預設顯示公斤數，隱藏流水號
        show_serial = st.checkbox("顯示流水號", value=False)
        
        display_cols = ["等級", "小代", "件數", "公斤", "單價", "買家"]
        if show_serial:
            display_cols.insert(0, "流水號")

        # 顯示大表格
        st.dataframe(
            df[display_cols], 
            use_container_width=True, 
            height=600,
            column_config={"單價": st.column_config.NumberColumn("單價", format="%d 元")}
        )
        
        st.metric("今日 F22 總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("找不到符合的 F22 資料。")