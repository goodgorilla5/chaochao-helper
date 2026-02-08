import streamlit as st
import pandas as pd
import io

# 1. 網頁基本設定
st.set_page_config(page_title="燕巢-台北現場助手", layout="centered")

# 2. 核心解析邏輯 (維持不變)
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

# 針對連結失效的貼心教學
with st.expander("📌 如何獲取資料 (點開看教學)", expanded=True):
    st.write("1. 若點擊連結無反應，請手動搜尋 **『AMIS 下載』** 或開啟瀏覽器輸入：")
    st.code("amis.afa.gov.tw")
    st.write("2. 點選：**資料下載** > **蔬果共同運銷資料下載**")
    st.write("3. 選擇：**台北市場**、單位 **S00076**、格式 **4碼品名(SCP)**")
    st.markdown("[👉 點我嘗試開啟下載頁面](https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx)")

# 上傳區塊
uploaded_file = st.file_uploader("📂 下載完成後，請在此上傳檔案", type=['scp', 'txt'])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8", errors="ignore")
    data = process_logic(content)
    
    if data:
        df = pd.DataFrame(data)
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            q = st.text_input("🔍 搜尋小代", placeholder="後3碼")
        with col2:
            sort_opt = st.selectbox("單價排序", ["高 → 低", "低 → 高"])

        if q:
            df = df[df['小代'].str.contains(q)]
        df = df.sort_values(by="單價", ascending=(sort_opt == "低 → 高"))

        st.dataframe(df, use_container_width=True, height=500)
        st.metric("當前畫面總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("找不到 F22 資料，請確認檔案。")

st.markdown("---")
st.caption("燕巢農會台北市場專用工具 | 已優化手機瀏覽")