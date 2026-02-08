import streamlit as st
import pandas as pd
import os
import glob
import time

st.set_page_config(page_title="燕巢台北對帳-本地秒開版", layout="wide")

# 解析邏輯 (維持最強兼容性)
def parse_scp_logic(content):
    final_rows = []
    lines = content.split('\n')
    for line in lines:
        if "F22" in line:
            parts = line.replace('+', ' ').split()
            try:
                final_rows.append({
                    "小代": str(parts[3])[-3:],
                    "件數": int(parts[5].lstrip('0') or 0),
                    "公斤": int(parts[6].lstrip('0') or 0),
                    "單價": int(parts[7].lstrip('0')[:-1] or 0),
                    "買家": parts[-1]
                })
            except: continue
    return final_rows

st.title("🍎 燕巢農會 - 台北對帳自動看板")

# --- 側邊欄：手動上傳或說明 ---
st.sidebar.header("⚙️ 系統設定")
amis_url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
st.sidebar.markdown(f"[🔗 點我開啟農委會下載頁]({amis_url})")
st.sidebar.info("💡 只要把下載好的檔案丟進電腦的『燕巢對帳系統』資料夾，網頁就會自動更新。")

# --- 自動偵測資料夾內的檔案 ---
# 尋找當前目錄下最新的 txt 或 scp 檔案
target_files = glob.glob("*.txt") + glob.glob("*.scp")

if target_files:
    # 抓最新的一份
    latest_file = max(target_files, key=os.path.getmtime)
    file_mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(latest_file)))
    
    st.success(f"📅 自動讀取最新檔案：`{latest_file}` (存檔時間：{file_mtime})")

    with open(latest_file, 'r', encoding='utf-8', errors='ignore') as f:
        data = parse_scp_logic(f.read())

    if data:
        df = pd.DataFrame(data).sort_values("單價", ascending=False)
        
        # 指標顯示
        c1, c2, c3 = st.columns(3)
        c1.metric("總件數", f"{df['件數'].sum()} 件")
        c2.metric("最高單價", f"{df['單價'].max()} 元")
        c3.metric("總公斤", f"{df['公斤'].sum()} kg")

        st.divider()
        
        # 快速搜尋
        search = st.text_input("🔍 快速搜尋小代後 3 碼 (例如: 025)")
        if search:
            df = df[df['小代'].str.contains(search)]

        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.warning("⚠️ 檔案讀取成功，但裡面沒有台北 F22 的資料。")
else:
    st.error("❌ 資料夾內找不到任何資料檔案 (.txt 或 .scp)")
    st.info("請先手動下載一份檔案放到『燕巢對帳系統』資料夾內。")

st.markdown("---")
st.caption("本網頁自動同步電腦資料夾檔案 | 無須重複連線農委會")