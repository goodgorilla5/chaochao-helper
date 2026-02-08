import streamlit as st
import pandas as pd

st.set_page_config(page_title="燕巢台北對帳助手", layout="centered")

# 核心解析邏輯
def parse_scp(content):
    rows = []
    lines = content.split('\n')
    for line in lines:
        if "F22" in line:
            parts = line.replace('+', ' ').split()
            try:
                rows.append({
                    "小代": str(parts[3])[-3:], 
                    "件數": int(parts[5].lstrip('0') or 0),
                    "單價": int(parts[7].lstrip('0')[:-1] or 0),
                    "買家": parts[-1]
                })
            except: continue
    return rows

st.title("🍎 燕巢農會對帳系統")

# --- 第一步：聰明的下載按鈕 ---
st.subheader("第一步：下載最新資料")
st.info("請先點擊下方按鈕，會自動幫你跳轉並準備好下載。")

# 這裡利用 HTML 建立一個直接連往農委會並帶有指令的提示
amis_url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"
st.markdown(f"""
    <a href="{amis_url}" target="_blank">
        <button style="width:100%; height:60px; background-color:#ff4b4b; color:white; border:none; border-radius:10px; font-size:20px; font-weight:bold; cursor:pointer;">
            🚀 開啟農委會下載頁面
        </button>
    </a>
    <p style='color:gray; font-size:14px; margin-top:10px;'>
        (註：進入後請確保切換至「電腦版網站」，並點擊書籤執行自動填寫)
    </p>
""", unsafe_allow_stdio=True)

st.divider()

# --- 第二步：極速分析 ---
st.subheader("第二步：查看對帳結果")
uploaded_file = st.file_uploader("📂 請點此選擇剛下載的檔案", type=['scp', 'txt'])

if uploaded_file:
    raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
    data = parse_scp(raw_text)
    
    if data:
        df = pd.DataFrame(data)
        
        # 搜尋功能
        search = st.text_input("🔍 搜尋小代編號", placeholder="輸入後三碼")
        if search:
            df = df[df['小代'].str.contains(search)]
        
        # 排序：高單價在前
        df = df.sort_values(by="單價", ascending=False)
        
        # 統計資訊
        st.metric("當前畫面總件數", f"{df['件數'].sum()} 件")
        
        # 表格大字體優化
        st.dataframe(df, use_container_width=True, height=500)
    else:
        st.warning("檔案中找不到 F22 資料，請確認農委會下載時是否選對「台北市場」。")