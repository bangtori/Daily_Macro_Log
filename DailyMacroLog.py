import yfinance as yf
from datetime import datetime, timedelta
import requests
import os

# ==========================================
# 🔐 사용자 설정
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
# ==========================================

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

# ---------------------------------------------------------
# 🌞 아침용: 전체 대시보드 
# ---------------------------------------------------------
def get_morning_report(today_str):
    # 섹션 1: 매크로 & 코인
    tickers_1 = {
        "🇺🇸 국채 10년물": "^TNX",
        "🇰🇷 환율 (원/달러)": "KRW=X",
        "🛢️ 유가 (WTI)": "CL=F",
        "🥇 금 (Gold)": "GC=F",
        "🥉 구리 (Copper)": "HG=F",
        "🥈 은 (Silver)": "SI=F",
        "🪙 코인 (BTC)": "BTC-USD"
    }
    # 섹션 2: 주요 지수
    tickers_2 = {
        "🇺🇸 S&P 500": "^GSPC",
        "🇺🇸 나스닥": "^IXIC",
        "🇺🇸 러셀 2000": "^RUT",
        "🇰🇷 코스피": "^KS11",
        "🇰🇷 코스닥": "^KQ11",
        "⚙️ 필라반도체 (SOX)": "^SOX",
        "😱 공포지수 (VIX)": "^VIX"
    }

    msg = "```markdown\n"
    msg += f"# 📅 {today_str} 경제 대시보드\n\n"
    
    # [Table 1]
    msg += "## 1. 📊 오늘의 4대 지표 (System Status)\n"
    msg += "| 지표 | 현재가 | 전일비 | 상태 (Signal) |\n"
    msg += "| :--- | :--- | :--- | :--- |\n"
    
    print("🌞 아침 리포트 생성 중...")
    
    for name, symbol in tickers_1.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if len(hist) < 2: continue
            
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            diff_pct = ((curr - prev) / prev) * 100
            
            if symbol == "^TNX": price = f"{curr:.2f}%"
            elif symbol == "KRW=X": price = f"{curr:,.0f}원"
            else: price = f"{curr:.2f}"
            
            if diff_pct > 0: icon = "🔺"
            elif diff_pct < 0: icon = "🔻"
            else: icon = "➖"
            diff_str = f"{icon} {abs(diff_pct):.2f}%"
            
            sig = " "
            if symbol == "^TNX":
                if diff_pct > 3.0: sig = "⚠️ 발작"
                elif diff_pct < -3.0: sig = "🔥 추락"
                elif curr < 3.5 or curr > 4.5: sig = "⚠️ 이탈"
                else: sig = "안정"
            elif symbol == "KRW=X":
                if curr >= 1450: sig = "⚠️ 위험"
                elif curr <= 1400: sig = "🍬 줍줍"
                else: sig = "Normal"
            elif symbol == "CL=F" and curr < 60: sig = "📉 침체"

            msg += f"| **{name}** | {price} | {diff_str} | {sig} |\n"
        except: continue

    # [Table 2]
    msg += "\n## 2. 오늘의 주요 지수\n"
    msg += "| 지수 | 현재가 | 전일비 | 원인 |\n"
    msg += "| :--- | :--- | :--- | :--- |\n"

    for name, symbol in tickers_2.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if len(hist) < 2: continue
            
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            diff_pct = ((curr - prev) / prev) * 100
            
            price = f"{curr:,.2f}"
            if diff_pct > 0: icon = "🔺"
            elif diff_pct < 0: icon = "🔻"
            else: icon = "➖"
            diff_str = f"{icon} {abs(diff_pct):.2f}%"

            msg += f"| **{name}** | {price} | {diff_str} | |\n"
        except: continue

    msg += "```"
    send_telegram_message(msg)

# ---------------------------------------------------------
# 🌙 오후용: 국내장 마감 브리핑 
# ---------------------------------------------------------
def get_closing_report(today_str):
    target_tickers = {
        "🇰🇷 코스피": "^KS11",
        "🇰🇷 코스닥": "^KQ11",
        "🇰🇷 환율": "KRW=X"
    }
    
    msg = "```markdown\n"
    msg += f"# 🇰🇷 {today_str} 국내증시 마감\n\n"
    msg += "| 지수 | 현재가 | 전일비 | 비고 |\n"
    msg += "| :--- | :--- | :--- | :--- |\n"
    
    print("🌙 마감 리포트 생성 중...")
    
    for name, symbol in target_tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if len(hist) < 2: continue
            
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            diff_pct = ((curr - prev) / prev) * 100
            
            if symbol == "KRW=X": price = f"{curr:,.0f}원"
            else: price = f"{curr:,.2f}"
            
            if diff_pct > 0: icon = "🔺"
            elif diff_pct < 0: icon = "🔻"
            else: icon = "➖"
            diff_str = f"{icon} {abs(diff_pct):.2f}%"
            
            # 간단 코멘트
            note = ""
            if abs(diff_pct) > 1.0:
                 note = "🔥 급등" if diff_pct > 0 else "💧 급락"

            msg += f"| **{name}** | {price} | {diff_str} | {note} |\n"
        except: continue
        
    msg += "```"
    send_telegram_message(msg)

# ---------------------------------------------------------
# 🚀 메인 실행 로직 (시간 체크)
# ---------------------------------------------------------
if __name__ == "__main__":
    # GitHub Actions 등 서버 시간(UTC)을 고려해 KST로 변환
    now_utc = datetime.utcnow()
    now_kst = now_utc + timedelta(hours=9)
    
    today_str = now_kst.strftime("%Y-%m-%d")
    current_hour = now_kst.hour

    print(f"🕒 현재 시간(KST): {current_hour}시")

    if current_hour >= 15:
        # 오후 3시 이후 실행 시 -> 마감 리포트
        get_closing_report(today_str)
    else:
        # 그 외 시간(아침) 실행 시 -> 전체 대시보드
        get_morning_report(today_str)