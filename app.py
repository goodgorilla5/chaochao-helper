import streamlit as st
import pandas as pd

# 設定網頁標題與寬度
st.set_page_config(page_title="燕巢台北對帳助手", layout="wide")

# 解析 SCP 的核心邏輯
def parse_scp(content):
    rows = []
    lines = content.split('\n')
    for line in lines:
        if "F22" in line:
            parts = line.replace('+', ' ').split()
            try:
                # 提取：小代(3碼)、件數、公斤、單價、買家
                rows.append({
                    "小代": str(parts[3])[-3:], 
                    "件數": int(parts[5].lstrip('0') or 0),
                    "單價": int(parts[7].lstrip('0')[:-1] or 0),
                    "買家": parts[-1]
                })
            except: continue
    return rows

# --- 側邊欄：操作教學 ---
with st.sidebar:
    st.header("⚡ 快速操作")
    st.markdown("1. **點擊下方連結**前往農委會")
    st.page_link("https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx", label="🔗 前往農委會下載頁", icon="🚀")
    st.write("---")
    st.write("2. **執行書籤** (填好 S00076)")
    st.write("3. **回到這裡** 上傳檔案")

# --- 主畫面 ---
st.title("🍎 燕巢農會 - 現場對帳助手")

# 這裡就是你想要的「抓取」按鈕：改為「檔案上傳器」
# 只要檔案一丟進去，它就會自動「抓取」裡面的內容並輸出結果
uploaded_file = st.file_uploader("📥 請將下載好的 SCP 檔案拖到這裡", type=['scp', 'txt'])

if uploaded_file:
    # 自動抓取並解析
    raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
    data = parse_scp(raw_text)
    
    if data:
        df = pd.DataFrame(data)
        
        # 搜尋功能
        st.subheader("🔍 快速對帳區")
        col1, col2 = st.columns([1, 1])
        with col1:
            search = st.text_input("搜尋小代 (後3碼)", placeholder="例如: 019")
        
        if search:
            df = df[df['小代'].str.contains(search)]
        
        # 排序：單價高到低
        df = df.sort_values(by="單價", ascending=False)

        # 顯示統計數據
        total_q = df['件數'].sum()
        st.success(f"✅ 抓取成功！目前畫面上共計: {total_q} 件")
        
        # 顯示大表格
        st.dataframe(df, use_container_width=True, height=600)
    else:
        st.error("此檔案格式不正確，或不含台北市場 (F22) 的資料。")
else:
    # 沒上傳時顯示的歡迎畫面
    st.info("👋 期待您的資料！請先從側邊欄下載檔案後上傳。")