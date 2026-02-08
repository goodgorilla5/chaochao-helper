import streamlit as st
import pandas as pd
import io

# 這裡放入你之前的邏輯
def process_logic(content):
    clean_content = content.replace('+', ' ')
    elements = clean_content.split()
    final_rows = []
    current_row = []
    
    for item in elements:
        if item.startswith('A') and current_row:
            if "F22" in current_row:
                try:
                    cleaned = [
                        str(current_row[3])[-3:],             # 小代
                        int(current_row[5].lstrip('0') or 0), # 件數
                        int(current_row[6].lstrip('0') or 0), # 公斤
                        int(current_row[7].lstrip('0')[:-1] or 0), # 單價
                        str(current_row[-1])                  # 買家
                    ]
                    final_rows.append(cleaned)
                except: pass
            current_row = []
        
        if len(item) > 3 and item[0:2].isdigit() and item[2].isalpha():
            current_row.append(item[:2])
            current_row.append(item[2:])
        else:
            current_row.append(item)
    return final_rows

st.title("家事達人極簡轉換器")
st.write("請上傳您的 .scp 檔案，轉換後將自動產出 Excel")

uploaded_file = st.file_uploader("選擇檔案", type=['scp', 'txt'])

if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8", errors="ignore")
    data = process_logic(content)
    
    if data:
        df = pd.DataFrame(data, columns=['小代', '件數', '公斤', '單價', '買家'])
        
        # 轉換為 Excel 二進位流
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        
        st.success("轉換成功！")
        st.download_button(
            label="點我下載 Excel 檔案",
            data=output.getvalue(),
            file_name="極簡對帳版.xlsx",
            mime="application/vnd.ms-excel"
        )