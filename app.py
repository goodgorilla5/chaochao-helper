import streamlit as st
import pandas as pd
import os
import glob
import time
import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By

st.set_page_config(page_title="燕巢對帳-全自動版", layout="wide")

# 計算今天的民國年檔名 (例如 1150208)
def get_today_filename():
    now = datetime.datetime.now()
    roc_year = now.year - 1911
    return f"{roc_year}{now.strftime('%m%d')}"

# 解析 SCP 內容
def parse_scp(content):
    rows = []
    for line in content.split('\n'):
        if "F22" in line:
            p = line.replace('+', ' ').split()
            try:
                rows.append({
                    "小代": str(p[3])[-3:],
                    "件數": int(p[5].lstrip('0') or 0),
                    "單價": int(p[7].lstrip('0')[:-1] or 0),
                    "買家": p[-1]
                })
            except: continue
    return rows

# 自動搬運工 (隱藏視窗)
def auto_fetch():
    options = Options()
    options.add_argument('--headless') # 靜默執行，不干擾你用電腦
    current_dir = os.getcwd()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", current_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/plain,application/octet-stream")

    try:
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get("https://amis.afa.gov.tw/download/DownloadVegFruitCoopData2.aspx")
        time.sleep(3)
        
        # 根據你提供的原始碼自動填寫
        driver.execute_script("document.getElementById('ctl00_contentPlaceHolder_txtSupplyNo').value = 'S00076 燕巢區農會';")
        driver.execute_script("document.getElementById('ctl00_contentPlaceHolder_hfldSupplyNo').value = 'S00076';")
        
        # 點擊你發現的 btnQuery2 按鈕
        btn = driver.find_element(By.ID, "ctl00_contentPlaceHolder_btnQuery2")
        btn.click()
        
        time.sleep(10) # 等待下載完成
        driver.quit()
        return True
    except:
        return False

st.title("🍎 燕巢農會 - 台北自動對帳看板")

# --- 檢查與執行區 ---
today_file_prefix = get_today_filename()
# 搜尋資料夾內是否有今天的檔名 (不論副檔名是 .txt 還是 .SCP)
today_files = glob.glob(f"*{today_file_prefix}*")

if not today_files:
    with st.spinner("🔄 偵測到今日尚未抓取，正在自動從農委會搬運資料..."):
        auto_fetch()
        st.rerun()

# --- 顯示區 ---
files = glob.glob("*.txt") + glob.glob("*.SCP") + glob.glob("*.scp")
if files:
    latest_file = max(files, key=os.path.getmtime)
    st.info(f"📅 目前顯示：{os.path.basename(latest_file)}")

    with open(latest_file, 'r', encoding='utf-8', errors='ignore') as f:
        df = pd.DataFrame(parse_scp(f.read()))

    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("今日總件數", f"{df['件數'].sum()} 件")
        c2.metric("最高單價", f"{df['單價'].max()} 元")
        
        search = st.text_input("🔍 搜尋小代後3碼 (如: 025)")
        if search:
            df = df[df['小代'].str.contains(search)]
        
        st.dataframe(df.sort_values("單價", ascending=False), use_container_width=True, height=600)
    else:
        st.warning("⚠️ 檔案已下載，但農委會尚未更新今日台北 F22 資料。")
else:
    st.error("❌ 暫無資料。請確保電腦連線正常。")