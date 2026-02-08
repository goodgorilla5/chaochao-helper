import streamlit as st
import pandas as pd
import re

# 設定手機版顯示優化
st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

def process_logic(content):
    # SCP 檔案每筆資料通常由四個空格區分
    raw_lines = content.split('    ')
    final_rows = []
    
    for line in raw_lines:
        # 只鎖定 F22 且是燕巢農會 S00076
        if "F22" in line and "S00076" in line:
            try:
                # --- 變通處理流水號：日期格之前的所有內容 ---
                # 尋找日期格（例如 11502081 或 11502071）
                # 邏輯：找到 S00076，往前找最近的一串 8 位數字且以 1 結尾的標記
                date_match = re.search(r"(\d{7,8}1)\s+\d{2}S00076", line)
                
                if date_match:
                    date_pos = date_match.start()
                    # 1. 抓取日期前方的所有內容作為流水號
                    raw_serial = line[:date_pos].strip()
                    # 2. 消除中間所有空格，合併成完整長字串
                    serial = raw_serial.replace(" ", "")
                    
                    # 剩餘部分用來抓取其他資訊
                    remaining = line[date_pos:]
                    s_pos = remaining.find("S00076")
                    
                    # 輪：S00076 前兩位數的第一位 (例如 21S 裡的 2)
                    turn = remaining[s_pos-2]
                    
                    # 小代：S00076 後面 3 位
                    sub_id = remaining[s_pos+6:s_pos+9]
                    
                    # 處理 + 號數字塊
                    nums = line.split('+')
                    pieces = int(nums[0][-3:].lstrip('0') or 0)
                    weight = int(nums[1].lstrip('0') or 0)
                    
                    # 單價修正：去掉最後一個 0 (如 00900 -> 90)
                    price_raw = nums[2].lstrip('0')
                    price = int(price_raw[:-1] if price_raw else 0)
                    
                    # 買家：最後一個 + 號後的 4 位數
                    buyer = nums[5].strip()[:4]

                    final_rows.append({
                        "流水號": serial,
                        "輪": turn,
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
    # 嘗試不同編碼讀取
    try:
        content = uploaded_file.read().decode("big5", errors="ignore")
    except:
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        
    data = process_logic(content)
    
    if data:
        df = pd.DataFrame(data)

        # --- 功能區：搜尋與排序 ---
        st.divider()
        col1, col2 = st.columns([1, 1])
        with col1:
            search_query = st.text_input("🔍 搜尋小代", placeholder="輸入如 605")
        with col2:
            sort_order = st.selectbox("排序單價", ["由高至低", "由低至高"])

        # 過濾特定小代
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        # 執行排序邏輯
        df = df.sort_values(by="單價", ascending=(sort_order == "由低至高"))

        # --- 顯示區 ---
        st.subheader("📋 交易資料清單")
        # 設定流水號欄位不被截斷
        st.dataframe(
            df, 
            use_container_width=True, 
            height=500,
            column_config={
                "流水號": st.column_config.TextColumn("流水號", width="large"),
                "單價": st.column_config.NumberColumn("單價", format="%d 元"),
            }
        )
        
        st.metric("當前 F22 總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("找不到符合的 F22 資料。")