import streamlit as st
import pandas as pd
import re
import requests
import time

st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

def process_logic(content):
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    
    # 使用 F22 作為每一筆交易的起點，不依賴空格數量
    parts = content.split('F22')
    for p in parts[1:]:
        if "S00076" in p:
            try:
                # 1. 抓取流水號 (找日期格之前的數字串)
                date_match = re.search(r"(\d{7,8}1)", p)
                if not date_match: continue
                date_pos = date_match.start()
                serial = p[:date_pos].strip().replace(" ", "")
                
                # 2. 抓取等級與小代 (以 S00076 為定位)
                s_pos = p.find("S00076")
                level_code = p[s_pos-2]
                level = grade_map.get(level_code, level_code)
                sub_id = p[s_pos+6:s_pos+9]
                
                # 3. 利用 + 號精準切割數字，完全防止位移錯誤
                nums = p.split('+')
                # 件數 (抓第一個+號前的最後三位數字)
                pieces = int(re.sub(r"\D", "", nums[0])[-3:] or 0)
                # 公斤 (抓第二個+號前的數字)
                weight = int(re.sub(r"\D", "", nums[1]) or 0)
                # 單價 (抓第三個+號前的數字，並去掉最後一位0)
                price_raw = re.sub(r"\D", "", nums[2])
                price = int(price_raw[:-1] if price_raw else 0)
                
                # 4. 買家 (最後一個+號後的前四位)
                buyer = nums[5].strip()[:4]

                final_rows.append({
                    "流水號": serial, "等級": level, "小代": sub_id, 
                    "件數": pieces, "公斤": weight, "單價": price, "買家": buyer
                })
            except:
                continue
    return final_rows

st.title("🍎 燕巢-台北現場對帳")

# --- 自動讀取 GitHub 檔案 ---
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

if auto_content and len(auto_content) > 100:
    st.success("✅ 已自動載入今日雲端資料")
    with st.expander("手動上傳備案"):
        manual_file = st.file_uploader("上傳 SCP 檔案", type=['scp', 'txt'])
        if manual_file:
            final_content = manual_file.read().decode("big5", errors="ignore")
    if not final_content:
        final_content = auto_content
else:
    st.warning("⚠️ 雲端目前無資料，請手動上傳。")
    manual_file = st.file_uploader("📂 手動上傳 SCP 檔案", type=['scp', 'txt'])
    if manual_file:
        final_content = manual_file.read().decode("big5", errors="ignore")

# --- 顯示結果 ---
if final_content:
    data = process_logic(final_content)
    if data:
        df = pd.DataFrame(data)
        st.divider()
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            search_query = st.text_input("🔍 搜尋小代", placeholder="如 605")
        with c2:
            # 加入「不排序」選項來維持原始流水號順序
            sort_order = st.selectbox("單價排序", ["預設(按流水號)", "價格：由高至低", "價格：由低至高"])
        with c3:
            show_serial = st.checkbox("顯示流水號", value=False)

        # 篩選
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        # 排序邏輯
        if sort_order == "價格：由高至低":
            df = df.sort_values(by="單價", ascending=False)
        elif sort_order == "價格：由低至高":
            df = df.sort_values(by="單價", ascending=True)
        # 預設則不執行 sort_values，維持讀取時的流水號順序

        display_cols = ["等級", "小代", "件數", "公斤", "單價", "買家"]
        if show_serial:
            display_cols.insert(0, "流水號")

        st.dataframe(
            df[display_cols], 
            use_container_width=True, 
            height=600,
            column_config={"單價": st.column_config.NumberColumn("單價", format="%d 元")}
        )
        
        st.metric("今日 F22 總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("找不到符合的 F22 資料。")