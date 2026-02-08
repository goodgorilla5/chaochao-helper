import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="燕巢台北對帳助手", layout="centered")

# 解析邏輯
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

st.title("🍎 燕巢農會對帳助手")

# --- 第一步：下載區 ---
st.subheader("第一步：下載最新資料")

amis_url = "https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx"

# 使用 HTML Component 來避開 markdown 報錯，這能確保按鈕 100% 顯示
components.html(
    f"""
    <a href="{amis_url}" target="_blank" style="text-decoration: none;">
        <button style="width:100%; height:60px; background-color:#ff4b4b; color:white; border:none; border-radius:10px; font-size:20px; font-weight:bold; cursor:pointer; font-family: sans-serif;">
            🚀 開啟農委會下載頁面
        </button>
    </a>
    """,
    height=80,
)

with st.expander("📌 點我複製「一鍵填寫」書籤代碼"):
    st.write("請複製下方代碼，存入手機書籤：")
    st.code("""javascript:(function(){var t=document.getElementById('ctl00_contentPlaceHolder_txtSupplyNo'),h=document.getElementById('ctl00_contentPlaceHolder_hfldSupplyNo'),b=document.getElementById('ctl00_contentPlaceHolder_btnQuery2');if(t&&h){t.value='S00076 燕巢區農會';h.value='S00076';if(b)b.click();}else{alert('請先切換至電腦版網頁');}})();""")

st.divider()

# --- 第二步：分析區 ---
st.subheader("第二步：上傳並對帳")
uploaded_file = st.file_uploader("📂 點此選擇剛下載的 SCP 檔案", type=['scp', 'txt'])

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
        
        # 表格顯示
        st.dataframe(df, use_container_width=True, height=500)
    else:
        st.warning("檔案中找不到 F22 資料，請確認下載時是否選對「台北市場」。")