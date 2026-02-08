import streamlit as st
import pandas as pd
import re

# 手機版優化
st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

def process_logic(content):
    # SCP 檔案每筆資料由四個空格區分
    raw_lines = content.split('    ')
    final_rows = []
    # 等級對照：1=特, 2=優, 3=良
    grade_map = {"1": "特", "2": "優", "3": "良"}
    
    for line in raw_lines:
        # 鎖定 F22 與 燕巢農會 S00076
        if "F22" in line and "S00076" in line:
            try:
                # 定位日期標記 (例如 11502081)
                date_match = re.search(r"(\d{7,8}1)\s+\d{2}S00076", line)
                
                if date_match:
                    date_pos = date_match.start()
                    # 1. 抓取日期前內容，消除空格合併成流水號
                    raw_serial = line[:date_pos].strip()
                    serial = raw_serial.replace(" ", "")
                    
                    remaining = line[date_pos:]
                    s_pos = remaining.find("S00076")
                    
                    # 2. 轉換等級 (1,2,3 -> 特,優,良)
                    raw_turn = remaining[s_pos-2]
                    level = grade_map.get(raw_turn, raw_turn)
                    
                    # 3. 小代 (S00076 後面 3 位)
                    sub_id = remaining[s_pos+6:s_pos+9]
                    
                    # 4. 處理數字塊
                    nums = line.split('+')
                    pieces = int(nums[0][-3:].lstrip('0') or 0)
                    weight = int(nums[1].lstrip('0') or 0)
                    
                    # 5. 單價修正：00900 -> 90 (去掉最後一個 0)
                    price_raw = nums[2].lstrip('0')
                    price = int(price_raw[:-1] if price_raw else 0)
                    
                    # 6. 買家 (最後一個 + 號後的 4 位)
                    buyer = nums[5].strip()[:4]

                    final_rows.append({
                        "流水號": serial, "等級": level, "小代": sub_id,
                        "件數": pieces, "公斤": weight, "單價": price, "買家": buyer
                    })
            except:
                continue
    return final_rows

st.title("🍎 燕巢-台北現場對帳")

# 直接放置上傳按鈕，不再預設抓取，避免黑畫面
uploaded_file = st.file_uploader("📂 請上傳 SCP 檔案", type=['scp', 'txt', 'SCP'])

if uploaded_file:
    try:
        content = uploaded_file.read().decode("big5", errors="ignore")
    except:
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        
    data = process_logic(content)
    
    if data:
        df = pd.DataFrame(data)

        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            search_query = st.text_input("🔍 搜尋小代", placeholder="輸入如 605")
        with col2:
            sort_order = st.selectbox("排序單價", ["由高至低", "由低至高"])
        with col3:
            # 默認不勾選流水號
            show_serial = st.checkbox("顯示流水號", value=False)

        # 篩選小代
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        # 執行排序
        df = df.sort_values(by="單價", ascending=(sort_order == "由低至高"))

        # 控制顯示欄位
        display_cols = ["等級", "小代", "件數", "公斤", "單價", "買家"]
        if show_serial:
            display_cols.insert(0, "流水號")

        # 顯示清單
        st.subheader("📋 交易資料清單")
        st.dataframe(
            df[display_cols], 
            use_container_width=True, 
            height=500,
            column_config={
                "流水號": st.column_config.TextColumn("流水號", width="small"),
                "單價": st.column_config.NumberColumn("單價", format="%d 元"),
            }
        )
        
        st.metric("當前 F22 總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("找不到符合的 F22 資料。")
else:
    st.info("💡 請使用書籤下載 SCP 後，點擊上方按鈕上傳。")