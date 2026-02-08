import streamlit as st
import pandas as pd
import io

# 1. 網頁基本設定
st.set_page_config(page_title="燕巢-台北現場助手", layout="centered")

# 2. 核心解析邏輯 (保留不變)
def process_logic(content):
    clean_content = content.replace('+', ' ')
    elements = clean_content.split()
    final_rows = []
    current_row = []
    for item in elements:
        if item.startswith('A') and current_row:
            if "F22" in current_row:
                try:
                    cleaned = {
                        "小代": str(current_row[3])[-3:],             
                        "件數": int(current_row[5].lstrip('0') or 0), 
                        "公斤": int(current_row[6].lstrip('0') or 0), 
                        "單價": int(current_row[7].lstrip('0')[:-1] or 0), 
                        "買家": str(current_row[-1])                  
                    }
                    final_rows.append(cleaned)
                except: pass
            current_row = []
        if len(item) > 3 and item[0:2].isdigit() and item[2].isalpha():
            current_row.append(item[:2]); current_row.append(item[2:])
        else:
            current_row.append(item)
    return final_rows

# --- 3. 網頁介面 ---
st.title("🍎 燕巢-台北現場助手")

# 貼心提示：直接放下載連結
st.warning("⚠️ 若自動同步受阻，請點下方連結手動下載後上傳：")
st.markdown("[👉 點我前往農委會下載頁面](https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx)")

# 上傳區塊（大按鈕，手機好點）
uploaded_file = st.file_uploader("📂 請上傳下載好的 SCP 檔案", type=['scp', 'txt'])

if uploaded_file:
    # 讀取並轉換資料
    content = uploaded_file.read().decode("utf-8", errors="ignore")
    data = process_logic(content)
    
    if data:
        df = pd.DataFrame(data)
        
        st.divider()
        # 搜尋與排序（並排顯示）
        col1, col2 = st.columns(2)
        with col1:
            q = st.text_input("🔍 搜尋小代", placeholder="輸入後3碼")
        with col2:
            sort_opt = st.selectbox("單價排序", ["高 → 低", "低 → 高"])

        # 過濾與排序
        if q:
            df = df[df['小代'].str.contains(q)]
        df = df.sort_values(by="單價", ascending=(sort_opt == "低 → 高"))

        # 大表格顯示 (適合手機滑動)
        st.dataframe(df, use_container_width=True, height=500)
        
        # 大字體統計
        st.metric("當前畫面總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("檔案內找不到 F22 資料，請確認是否選錯檔案。")

st.markdown("---")
st.caption("燕巢農會台北市場專用工具 | 已優化手機瀏覽")