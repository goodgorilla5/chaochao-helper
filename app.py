import streamlit as st
import pandas as pd

# 設定手機版顯示優化
st.set_page_config(page_title="燕巢台北市場助手", layout="centered")

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

st.title("🍎 燕巢-台北現場對帳")

uploaded_file = st.file_uploader("請上傳 SCP 檔案", type=['scp', 'txt'])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8", errors="ignore")
    data = process_logic(content)
    
    if data:
        df = pd.DataFrame(data)

        # --- 功能區：搜尋與排序 ---
        st.divider()
        col1, col2 = st.columns([1, 1])
        
        with col1:
            search_query = st.text_input("🔍 搜尋小代", placeholder="輸入如 019")
        
        with col2:
            sort_order = st.selectbox("排序單價", ["由高至低", "由低至高"])

        # 執行過濾邏輯
        if search_query:
            df = df[df['小代'].str.contains(search_query)]
        
        # 執行排序邏輯
        if sort_order == "由高至低":
            df = df.sort_values(by="單價", ascending=False)
        else:
            df = df.sort_values(by="單價", ascending=True)

        # --- 顯示區 ---
        st.subheader("📋 交易資料清單")
        # 使用 st.dataframe 讓手機可以滑動查看，並設定高度
        st.dataframe(
            df, 
            use_container_width=True, 
            height=400,
            column_config={
                "小代": st.column_config.TextColumn("小代"),
                "單價": st.column_config.NumberColumn("單價", format="%d 元"),
            }
        )
        
        # 額外小功能：顯示總結
        st.metric("當前總件數", f"{df['件數'].sum()} 件")
    else:
        st.error("找不到 F22 資料，請確認檔案是否正確。")