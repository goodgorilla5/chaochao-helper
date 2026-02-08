import pandas as pd
import re
from datetime import datetime

def parse_amis_final(line):
    # 範例：A21150207470800111502077507132  11502071  31S00076575 F22  002+00024+00400+000000960+7000+0870
    try:
        # 1. 流水號 (A 開頭前 30 位)
        serial = line[0:30].strip()
        
        # 2. 輪 (由市場別 11, 21, 31 的第一位決定)
        # 位置在日期 11502071 之後的兩位數
        market_part = line[42:44] 
        turn = market_part[0] # 取出 1, 2 或 3
        
        # 3. 小代 (S00076 後面 3 位)
        sub_id_match = re.search(r"S00076(\d{3})", line)
        sub_id = sub_id_match.group(1) if sub_id_match else ""
        
        # 4. 拆解 + 號後面的數字塊
        nums = line.split('+')
        pieces = int(nums[0][-3:])      # 件數 (例如 002)
        weight = int(nums[1])           # 公斤 (例如 00024)
        price  = int(nums[2]) / 10      # 單價 (00400 變 40.0)
        # 去掉單價小數點後的 0 (例如 40.0 變 40)
        price = int(price) if price == int(price) else price
        
        # 5. 買家 (最後 4 位)
        buyer = nums[5][0:4]
        
        return {
            "流水號": serial,
            "輪": turn,
            "小代": sub_id,
            "件數": pieces,
            "公斤": weight,
            "單價": price,
            "買家": buyer
        }
    except:
        return None

def generate_perfect_report():
    # 讀取當天 SCP (例如 1150208.SCP)
    with open("1150208.SCP", "r", encoding="big5", errors="ignore") as f:
        content = f.read()
    
    # 解析所有行
    raw_lines = content.split('    ')
    data = [parse_amis_final(l) for l in raw_lines if parse_amis_final(l)]
    
    df = pd.DataFrame(data)
    
    # 按照你的需求排序：單價由高到低
    df = df.sort_values(by="單價", ascending=False)

    # 產出 HTML 網頁 (供 GitHub Pages 使用)
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>燕巢農會行情報表</title>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: sans-serif; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .highlight {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>燕巢農會 (S00076) 最終整理報表</h2>
        <p>更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        {df.to_html(index=False, classes='table')}
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_perfect_report()