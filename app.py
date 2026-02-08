import streamlit as st
import pandas as pd
import re
import requests
import time

st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

def process_logic(content):
    # 改回最穩定的分割方式
    raw_lines = content.split('    ')
    final_rows = []
    grade_map = {"1": "特", "2": "優", "3": "良"}
    
    for line in raw_lines:
        # 確保是 F22 且包含燕巢代號
        if "F22" in line and "S00076" in line:
            try:
                # 【核心錨點】：尋找日期標記 (例如 11502081)
                date_match = re.search(r"(\d{7,8}1)\s+\d{2}S00076", line)
                
                if date_match:
                    date_pos = date_match.start()
                    
                    # 1. 處理日期前的流水號：抓取內容並去除所有內建空格，防止位移
                    raw_serial_part = line[:date_pos].strip()
                    serial = raw_serial_part.replace(" ", "")
                    
                    # 2. 以日期後方的 S00076 定位等級與小代
                    remaining = line[date_pos:]
                    s_pos = remaining.find("S00076")
                    
                    # 等級 (S00076 前兩格)
                    raw_turn = remaining[s_pos-2]
                    level = grade_map.get(raw_turn, raw_turn)
                    
                    # 小代 (S00076 後三碼)
                    sub_id = remaining[s_pos+6:s_pos+9]
                    
                    # 3. 處理數字塊 (件數+公斤+單價)
                    nums = line.split('+')
                    # 件數：取加號前三位
                    pieces = int(nums[0][-3:].replace(" ", "") or 0)
                    # 公斤：取加號間數字
                    weight = int(nums[1].replace(" ", "") or 0)
                    
                    # 單價修正：00900 -> 90 (去掉最後一個 0)
                    price_raw = nums[2].strip().split(' ')[0] # 避免抓到後方買家代號
                    price = int(price_raw[:-1] if price_raw else 0)
                    
                    # 4. 買家：最後一個加號後的前四位
                    buyer = nums[5].strip()[:4]

                    final_rows.append({
                        "流水號": serial,
                        "等級": level,
                        "小代": sub_id,
                        "件數": pieces,
                        "公斤": weight,
                        "單價": price,
                        "買家": buyer
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
            search_query = st.text_input("🔍 搜尋小代", placeholder="如 627")
        with c2:
            # 預設維持讀取順序（流水號）
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