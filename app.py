import streamlit as st
import pandas as pd
import re
import requests
import time

# 頁面設定：手機版大字體優化
st.set_page_config(page_title="燕巢行情對帳", layout="centered")

# --- 完美解析邏輯 ---
def process_logic(content):
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    # 使用 F22 作為切割標記
    parts = content.split('F22')
    for p in parts[1:]:
        if "S00076" in p:
            try:
                # 尋找日期座標定位 (例如 11502081)
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
                
                # 單價修正：去掉最後一位 (1250 -> 125)
                price_raw = nums[2].lstrip('0')
                price = int(price_raw[:-1] if price_raw else 0)
                
                buyer = nums[5].strip()[:4]

                final_rows.append({
                    "等級": level, "小代": sub_id, "件數": pieces, 
                    "公斤": weight, "單價": price, "買家": buyer, "流水號": serial
                })
            except: continue
    return final_rows

st.title("🍎 燕巢-台北現場對帳")

# --- 從 GitHub 讀取今日資料 (強制刷新模式) ---
# 加上 ?t=時間戳記 是為了騙過瀏覽器，讓它以為是新網址，進而抓到最新檔案
timestamp = int(time.time())
RAW_URL = f"https://raw.githubusercontent.com/goodgorilla5/chaochao-helper/main/today.scp?t={timestamp}"

@st.cache_data(ttl=60) # 網頁端的快取也只保留 60 秒
def fetch_auto_data(url):
    try:
        # 加上 timeout 防止網頁卡死，headers 告訴 GitHub 不要給我舊快取
        r = requests.get(url, timeout=10, headers={'Cache-Control': 'no-cache'})
        if r.status_code == 200:
            return r.content.decode("big5", errors="ignore")
    except:
        return None
    return None

# 優先抓取自動更新檔
auto_content = fetch_auto_data(RAW_URL)
final_content = None

# 介面邏輯
if auto_content and len(auto_content) > 100:
    st.success("✅ 已自動同步今日行情")
    # 父母如果想自己傳，點開這個加號
    with st.expander("需要手動更換檔案？"):
        manual_file = st.file_uploader("上傳新的 SCP 檔案", type=['scp', 'txt'])
        if manual_file:
            final_content = manual_file.read().decode("big5", errors="ignore")
    
    if not final_content:
        final_content = auto_content
else:
    st.warning("⚠️ 雲端資料同步中，或資料尚未產生。")
    manual_file = st.file_uploader("📂 請點此手動上傳 SCP", type=['scp', 'txt'])
    if manual_file:
        final_content = manual_file.read().decode("big5", errors="ignore")

# --- 顯示結果 ---
if final_content:
    data = process_logic(final_content)
    if data:
        df = pd.DataFrame(data)
        st.divider()
        
        # 搜尋功能 (自動排版)
        search_query = st.text_input("🔍 搜尋小代 (例如: 605)", "")
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        # 預設單價由高到低排序，符合長輩看盤習慣
        df = df.sort_values(by="單價", ascending=False)
        
        # 欄位顯示控制
        show_all = st.checkbox("顯示公斤數與流水號", value=False)
        
        cols = ["等級", "小代", "件數", "單價", "買家"]
        if show_all:
            cols = ["流水號", "等級", "小代", "件數", "公斤", "單價", "買家"]

        # 顯示大表格
        st.dataframe(df[cols], use_container_width=True, height=600)
        
        # 底部統計
        c1, c2 = st.columns(2)
        c1.metric("總件數", f"{df['件數'].sum()} 件")
        c2.write(f"刷新時間: {pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
    else:
        st.error("讀取成功但格式不符，請確認是否為 F22 資料。")