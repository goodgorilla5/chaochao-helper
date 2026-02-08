import streamlit as st
import pandas as pd

st.set_page_config(page_title="燕巢台北對帳助手", layout="centered")

# 解析邏輯 (保持穩定)
def parse_scp_logic(content):
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

# --- 第一步：聰明下載 ---
st.subheader("第一步：獲取資料")

# 這段代碼會直接執行你提供的那串 PostBack 指令
download_script = """
javascript:(function(){
    var t=document.getElementById('ctl00_contentPlaceHolder_txtSupplyNo');
    var h=document.getElementById('ctl00_contentPlaceHolder_hfldSupplyNo');
    if(t && h){
        t.value='S00076 燕巢區農會';
        h.value='S00076';
        /* 執行你提供的下載指令 */
        WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions("ctl00$contentPlaceHolder$btnQuery2", "", true, "", "", false, true));
    } else {
        alert('請先開啟農委會下載頁面，並確保切換至電腦版網頁。');
    }
})();
"""

st.info("💡 操作說明：\n1. 點擊下方按鈕前往農委會。\n2. 在該網頁點擊您的「燕巢下載書籤」。")

st.page_link("https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx", label="🚀 開啟農委會下載網頁", icon="🌐")

with st.expander("📌 點我複製「燕巢專用下載書籤」代碼"):
    st.code(download_script.replace('\n', ''))
    st.caption("請將上方代碼存成瀏覽器書籤，名稱取名為『燕巢下載』")

st.divider()

# --- 第二步：分析 ---
st.subheader("第二步：上傳檔案")
uploaded_file = st.file_uploader("📂 選擇剛下載的 SCP/TXT 檔案", type=['scp', 'txt'])

if uploaded_file:
    raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
    data = parse_scp_logic(raw_text)
    
    if data:
        df = pd.DataFrame(data).sort_values("單價", ascending=False)
        st.success("✅ 解析成功")
        
        search = st.text_input("🔍 搜尋小代 (後3碼)")
        if search:
            df = df[df['小代'].str.contains(search)]
        
        c1, c2 = st.columns(2)
        c1.metric("總件數", f"{df['件數'].sum()} 件")
        if not df.empty:
            c2.metric("最高價", f"{df['單價'].max()} 元")
        
        st.dataframe(df, use_container_width=True, height=500)