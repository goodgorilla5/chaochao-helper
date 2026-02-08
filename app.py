import streamlit as st
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="燕巢 F22 行情監控", layout="wide")

st.title("📊 燕巢農會 (S00076) F22 專屬報表")

def parse_line(line):
    # 只抓取包含 S00076 且品項為 F22 的資料
    if "S00076" in line and "F22" in line:
        try:
            # 1. 流水號 (前 30 位)
            serial = line[0:30].strip()
            
            # 2. 輪 (日期 11502071 之後的那兩位數的第一位)
            market_part = line[42:44]
            turn = market_part[0]
            
            # 3. 小代 (S00076 後面 3 位)
            sub_id_match = re.search(r"S00076(\d{3})", line)
            sub_id = sub_id_match.group(1) if sub_id_match else ""
            
            # 4. 拆解 + 號後面的數字塊
            nums = line.split('+')
            pieces = int(nums[0][-3:])      # 件數
            weight = int(nums[1])           # 公斤
            # 單價修正：01250 -> 125 (除以 10)
            price = int(nums[2]) // 10     
            
            # 5. 買家 (最後 4 位)
            buyer = nums[5][0:4]
            
            return {
                "流水號": serial, "輪": turn, "小代": sub_id,
                "件數": pieces, "公斤": weight, "單價": price, "買家": buyer
            }
        except:
            return None
    return None

# --- 側邊欄設定 ---
st.sidebar.header("篩選條件")
target_sub_id = st.sidebar.text_input("輸入特定小代 (留空則顯示全部)", "")

uploaded_file = st.file_uploader("請上傳 SCP 檔案", type="SCP")

if uploaded_file:
    content = uploaded_file.read().decode('big5', errors='ignore')
    raw_lines = content.split('    ')
    
    # 解析並過濾 F22
    data = [parse_line(l) for l in raw_lines if parse_line(l)]
    df = pd.DataFrame(data)
    
    if not df.empty:
        # 如果使用者有輸入特定小代，執行篩選
        if target_sub_id:
            df = df[df["小代"] == target_sub_id]
            st.subheader(f"🔍 小代 {target_sub_id} 的 F22 行情")
        else:
            st.subheader("📋 全部 F22 行情列表")

        # 排序：單價由高到低
        df_sorted = df.sort_values(by="單價", ascending=False)
        
        st.dataframe(df_sorted, use_container_width=True)
        
        # 下載 CSV
        st.download_button("匯出此表", df_sorted.to_csv(index=False).encode('utf-8-sig'), "f22_data.csv")
    else:
        st.warning("找不到符合 F22 的資料。")
else:
    st.info("請上傳 SCP 檔案開始分析")