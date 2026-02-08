import streamlit as st
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="燕巢行情監控", layout="wide")

st.title("📊 燕巢農會 (S00076) 行情分析 (Streamlit 版)")

def parse_line(line):
    # 按照你教我的 Excel 邏輯精準拆解
    try:
        # 1. 流水號 (前 30 位)
        serial = line[0:30].strip()
        
        # 2. 輪 (日期 11502071 之後的那兩位數的第一位)
        # 範例：...11502071  31S... 這裡的 3 就是第 3 輪
        market_part = line[42:44]
        turn = market_part[0]
        
        # 3. 小代 (S00076 後面 3 位)
        sub_id_match = re.search(r"S00076(\d{3})", line)
        sub_id = sub_id_match.group(1) if sub_id_match else ""
        
        # 4. 拆解 + 號後面的數字塊
        nums = line.split('+')
        pieces = int(nums[0][-3:])      # 件數
        weight = int(nums[1])           # 公斤
        # 修正價格：01250 -> 125 (除以 10)
        price  = int(nums[2]) // 10     
        
        # 5. 買家 (最後 4 位)
        buyer = nums[5][0:4]
        
        return {
            "流水號": serial, "輪": turn, "小代": sub_id,
            "件數": pieces, "公斤": weight, "單價": price, "買家": buyer
        }
    except:
        return None

# 這裡是核心：讀取檔案並呈現
# 未來這裡會加上自動下載功能，現在我們先讓它能跑出你的 Excel 格式
uploaded_file = st.file_uploader("請上傳 SCP 檔案", type="SCP")

if uploaded_file:
    content = uploaded_file.read().decode('big5', errors='ignore')
    raw_lines = content.split('    ')
    data = [parse_line(l) for l in raw_lines if parse_line(l)]
    
    df = pd.DataFrame(data)
    
    # 排序：單價由高到低
    df_sorted = df.sort_values(by="單價", ascending=False)
    
    st.success(f"解析成功！共 {len(df_sorted)} 筆資料")
    st.dataframe(df_sorted, use_container_width=True)
    
    # 下載 CSV 備份
    st.download_button("匯出整理後的資料", df_sorted.to_csv(index=False).encode('utf-8-sig'), "data.csv")
else:
    st.info("請上傳 1150208.SCP 檔案來查看結果")