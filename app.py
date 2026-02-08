import streamlit as st
import pandas as pd
import re

# 設定手機版顯示優化
st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

def process_logic(content):
    # SCP 檔案每筆資料由四個空格區分
    raw_lines = content.split('    ')
    final_rows = []
    
    # 等級對照表
    grade_map = {"1": "特", "2": "優", "3": "良"}
    
    for line in raw_lines:
        if "F22" in line and "S00076" in line:
            try:
                # 定位日期格標記 (例如 11502081)
                date_match = re.search(r"(\d{7,8}1)\s+\d{2}S00076", line)
                
                if date_match:
                    date_pos = date_match.start()
                    # 抓取流水號並合併空格
                    raw_serial = line[:date_pos].strip()
                    serial = raw_serial.replace(" ", "")
                    
                    remaining = line[date_pos:]
                    s_pos = remaining.find("S00076")
                    
                    # 抓取等級 (原本的輪)
                    raw_turn = remaining[s_pos-2]
                    level = grade_map.get(raw_turn, raw_turn)
                    
                    # 小代
                    sub_id = remaining[s_pos+6:s_pos+9]
                    
                    # 處理數字塊
                    nums = line.split('+')
                    pieces = int(nums[0][-3:].lstrip('0') or 0)
                    weight = int(nums[1].lstrip('0') or 0)
                    
                    # 單價 (去掉最後一個 0)
                    price_raw = nums[2].lstrip('0')
                    price = int(price_raw[:-1] if price_raw else 0)
                    
                    # 買家
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

uploaded_file = st.file_uploader("請上傳 SCP 檔案", type=['scp', 'txt', 'SCP'])

if uploaded_file:
    try:
        content = uploaded_file.read().decode("big5", errors="ignore")
    except:
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        
    data = process_logic(content)
    
    if data:
        df = pd.DataFrame(data)

        st.divider()
        col1, col2 = st.columns([1, 1])
        with col1:
            search_query = st.text_input("🔍 搜尋小代", placeholder="輸入如 605")
        with col2:
            sort_order = st.selectbox("排序單價", ["由高至低", "由低至高"])

        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        df = df.sort_values(by="單價", ascending=(sort_order == "由低至高"))

        # --- 顯示區：控制欄位寬度 ---
        st.subheader("📋 交易資料清單")
        st.dataframe(
            df, 
            use_container_width=True, 
            height=500,
            column_config={
                "流水號": st.column_config.TextColumn("流水號", width="small"), # 縮小流水號
                "等級": st.column_config.TextColumn("等級", width="small"),
                "小代": st.column_config.TextColumn("小代", width="small"),
                "單價": st.column_config.NumberColumn("單價", format="%d 元", width="small"),
            }
        )
        
        st.metric("當前 F22 總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("找不到符合的 F22 資料。")