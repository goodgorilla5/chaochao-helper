import streamlit as st
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="燕巢-台北現場助手", layout="centered")

# 2. 核心解析邏輯 (不變)
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

# 強化的手機下載教學
with st.expander("🚨 手機找不到下載專區？請看這裏", expanded=True):
    st.error("手機版網頁會隱藏下載功能，請務必執行以下動作：")
    st.write("1. 點擊瀏覽器選單 (Chrome點三個點 / Safari點AA)")
    st.write("2. 勾選 **『切換電腦版網站』**")
    st.write("3. 看到電腦畫面後，選 **資料下載** > **蔬果共同運銷資料下載**")
    st.markdown("[👉 點我前往下載頁 (記得切換電腦版)](https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx)")



# 上傳區塊
uploaded_file = st.file_uploader("📂 下載完成後，請點此處上傳 SCP 檔案", type=['scp', 'txt'])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8", errors="ignore")
    data = process_logic(content)
    
    if data:
        df = pd.DataFrame(data)
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            q = st.text_input("🔍 搜尋小代", placeholder="輸入後3碼")
        with col2:
            sort_opt = st.selectbox("單價排序", ["高 → 低", "低 → 高"])

        if q:
            df = df[df['小代'].str.contains(q)]
        df = df.sort_values(by="單價", ascending=(sort_opt == "低 → 高"))

        # 大表格顯示
        st.dataframe(df, use_container_width=True, height=500)
        st.metric("當前畫面總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("檔案內找不到 F22 資料，請確認是否選錯檔案。")

st.markdown("---")
st.caption("燕巢農會台北市場專用工具")