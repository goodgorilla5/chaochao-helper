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
        # 只鎖定 F22 且是燕巢農會 S00076
        if "F22" in line and "S00076" in line:
            try:
                # --- 變通處理流水號：以日期格為基準 ---
                # 定位日期格 (如 11502081)
                date_match = re.search(r"(\d{7,8}1)\s+\d{2}S00076", line)
                
                if date_match:
                    date_pos = date_match.start()
                    # 1. 抓取日期前內容，消除空格合併成流水號
                    raw_serial = line[:date_pos].strip()
                    serial = raw_serial.replace(" ", "")
                    
                    # 2. 獲取剩餘資訊
                    remaining = line[date_pos:]
                    s_pos = remaining.find("S00076")
                    
                    # 3. 抓取原本的「輪」並轉換為「等級」
                    raw_turn = remaining[s_pos-2] # 取得 1, 2, 或 3
                    level = grade_map.get(raw_turn, raw_turn) # 轉成 特, 優, 良
                    
                    # 4. 小代 (S00076 後面 3 位)
                    sub_id = remaining[s_pos+6:s_pos+9]
                    
                    # 5. 處理 + 號數字塊
                    nums = line.split('+')
                    pieces = int(nums[0][-3:].lstrip('0') or 0) # 件數
                    weight = int(nums[1].lstrip('0') or 0)      # 公斤
                    
                    # 6. 單價修正：去掉最後一個 0 (如 00900 -> 90)
                    price_raw = nums[2].lstrip('0')
                    price = int(price_raw[:-1] if price_raw else 0)
                    
                    # 7. 買家
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
        content = uploaded_file.read().decode("utf-8", errors="ignore