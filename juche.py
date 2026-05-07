import os
import time
import pandas as pd
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import io

# --- [1. 시스템 설정] ---
# 소수점 2자리 설정 (저장되는 데이터에도 적용)
pd.options.display.float_format = '{:.2f}'.format

now_str = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

# 파일 경로 커스터마이징: 현재 폴더 기준
fileDir = 'kskq350.xlsx'
json_output = 'stock_data.json'

def get_max_consecutive_buy(series):
    """연속 순매수 일수 계산"""
    is_buy = series > 0
    groups = is_buy.ne(is_buy.shift()).cumsum()
    consecutive_counts = is_buy[is_buy].groupby(groups).size()
    return int(consecutive_counts.max()) if not consecutive_counts.empty else 0

options = webdriver.ChromeOptions()
options.add_argument('--headless') 
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 엑셀 파일 로드
df_file = pd.read_excel(fileDir)

print(f"🚩 [{now_str}] 분석 시작 (R5, R10, R20 수익률 포함)")

final_results = []

# --- [2. 메인 루프] ---
for symbol_full in df_file['symbols']:
    try:          
        name = symbol_full[7:]
        symbol = symbol_full[:6]
        
        url = f"https://m.stock.naver.com/domestic/stock/{symbol}/total"
        browser.get(url)
        time.sleep(0.7)
        
        # 데이터 확보를 위한 더보기 클릭
        for i in range(4): 
            try:
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                xpath_selector = "//*[contains(text(), '매매동향') and contains(text(), '더보기')]"
                btn = browser.find_element(By.XPATH, xpath_selector)
                browser.execute_script("arguments[0].click();", btn)                                                                                
                time.sleep(0.4)
            except:
                break
                                          
        html_source = io.StringIO(browser.page_source)        
        df_list = pd.read_html(html_source)
        if len(df_list) < 2: continue
        df_A = df_list[1] 

        # 숫자 데이터 정제
        cols_to_fix = ['종가', '외국인', '기관', '개인']
        for col in cols_to_fix:
            df_A[col] = pd.to_numeric(df_A[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)

        # 기타 주체 계산
        df_A['기타'] = -(df_A['개인'] + df_A['외국인'] + df_A['기관'])

        curr_price = int(df_A['종가'].iloc[0])
        
        def calc_ret(days):
            if len(df_A) > days:
                prev_price = df_A['종가'].iloc[days]
                if prev_price == 0: return 0.0
                # 소수점 2자리 반올림
                return round(((curr_price - prev_price) / prev_price) * 100, 2)
            return 0.0

        df_30 = df_A.head(30)
        df_30_seq = df_30.iloc[::-1]

        # 데이터 구조화 (R1 제외)
        res_dict = {
            'symbol': symbol,
            'name': name, # name[:5]
            'price': curr_price,
            'supply': {
                'individual': int((df_30['개인'] > 0).sum()),
                'foreign': int((df_30['외국인'] > 0).sum()),
                'institution': int((df_30['기관'] > 0).sum()),
                'other': int((df_30['기타'] > 0).sum())
            },
            'consecutive': {
                'individual': get_max_consecutive_buy(df_30_seq['개인']),
                'foreign': get_max_consecutive_buy(df_30_seq['외국인']),
                'institution': get_max_consecutive_buy(df_30_seq['기관']),
                'other': get_max_consecutive_buy(df_30_seq['기타'])
            },
            'returns': {
                'R5': calc_ret(5),
                'R10': calc_ret(10),
                'R20': calc_ret(20)
            }
        }
        
        final_results.append(res_dict)
        #######print(f"✅ 완료: {name}")

    except Exception as e:
        print(f"❌ 에러 ({symbol}): {e}")
        continue   

# --- [3. 결과 저장] ---
full_data = {
    "last_updated": now_str,
    "stocks": final_results
}

with open(json_output, 'w', encoding='utf-8') as f:
    json.dump(full_data, f, ensure_ascii=False, indent=4)

print(f"\n📂 JSON 파일 생성 완료: {os.path.abspath(json_output)}")
browser.quit()