import streamlit as st
import pandas as pd
import re
import requests

st.set_page_config(page_title="燕巢行情(自動同步版)", layout="centered")

def process_logic(content):
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    # 使用 F22 作為切割標記
    parts = content.split('F22')
    for p in parts[1:]:
        if "S00076" in p:
            try:
                # 尋找日期座標定位
                date_match = re.search(r"(\d{7,8}1)", p)
                if not date_match: continue
                date_pos = date_match.start()
                # 合併流水號
                serial = p[:date_pos].strip().replace(" ", "")
                s_pos = p.find("S00076")
                # 等級與小代
                level = grade_map.get(p[s_pos-2], p[s_pos-2])
                sub_id = p[s_pos+6:s_pos+9]
                # 數字區處理
                nums = p.split('+')
                pieces = int(nums[0][-3:].lstrip('0') or 0)
                weight = int(nums[1].lstrip('0') or 0)
                price = int(nums[2].lstrip('0')[:-1] or 0)
                buyer = nums[5].strip()[:4]

                final_rows.append({
                    "等級": level, "小代": sub_id, "件數": pieces, 
                    "公斤": weight, "單價": price, "買家": buyer, "流水號": serial
                })
            except: continue
    return final_rows

st.title("🍎 燕巢-台北現場對帳")

# --- 嘗試讀取 GitHub 自動更新檔 ---
RAW_URL = "https://raw.githubusercontent.com/goodgorilla5/chaochao-helper/main/today.scp"

@st.cache_data(ttl=600)
def fetch_auto_data():
    try:
        r = requests.get(RAW_URL, timeout=5)
        if r.status_code == 200 and len(r.text) > 100:
            return r.text
    except: return None
    return None

auto_content = fetch_auto_data()
final_content = None

# 介面邏輯：如果 GitHub 有資料就顯示，並提供「手動覆蓋」按鈕
if auto_content:
    st.success("✅ 已自動載入今日雲端資料")
    with st.expander("如有需要，可手動上傳檔案覆蓋"):
        manual_file = st.file_uploader("上傳新的 SCP 檔案", type=['scp', 'txt'])
        if manual_file:
            final_content = manual_file.read().decode("big5", errors="ignore")
    if not final_content:
        final_content = auto_content
else:
    st.warning("⚠️ 雲端目前無資料，請點擊下方手動上傳。")
    manual_file = st.file_uploader("📂 手動上傳 SCP 檔案", type=['scp', 'txt'])
    if manual_file:
        final_content = manual_file.read().decode("big5", errors="ignore")

# --- 顯示結果 ---
if final_content:
    data = process_logic(final_content)
    if data:
        df = pd.DataFrame(data)
        st.divider()
        search_query = st.text_input("🔍 查詢小代號", "")
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        # 預設單價由高到低
        df = df.sort_values(by="單價", ascending=False)
        
        # 顯示欄位
        st.dataframe(df[["等級", "小代", "件數", "單價", "買家"]], use_container_width=True, height=500)
        
        col1, col2 = st.columns(2)
        col1.metric("總件數", f"{df['件數'].sum()} 件")
        col2.write(f"資料更新時間: {pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M')}")