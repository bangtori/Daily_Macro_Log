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
# 🧠 상태 판별 로직 (Brain)
# ---------------------------------------------------------
def get_signal(symbol, curr, diff_pct):
    # 1. 미국채 10년물
    if symbol == "^TNX":
        if diff_pct > 3.0: return "⚠️ 발작"
        if diff_pct < -3.0: return "🔥 추락"
        if curr < 3.5 or curr > 4.5: return "⚠️ 이탈"
        return "안정"

    # 2. 환율 (원달러)
    if symbol == "KRW=X":
        if curr >= 1450: return "⚠️ 위험"
        if curr <= 1400: return "🍬 줍줍"
        if abs(diff_pct) > 0.5: return "🌊 변동"
        return "Normal"

    # 3. 달러 인덱스
    if "DX-Y" in symbol:
        if curr >= 105: return "👑 킹달러"
        if curr <= 100: return "⬇️ 약세"
        return "Normal"

    # 4. 유가
    if "CL=F" in symbol:
        if curr < 60: return "📉 침체"
        if curr > 85: return "🔥 인플레"
        return "Normal"

    # 5. 공포지수 (VIX)
    if "VIX" in symbol:
        if curr >= 30: return "😱 패닉"
        if curr >= 20: return "😨 공포"
        return "평온"

    # 6. 하이일드 (HYG) - 위험 선호 심리
    if "HYG" in symbol:
        if diff_pct > 0.2: return "Risk On"
        if diff_pct < -0.2: return "Risk Off"
        return "Normal"

    # 7. 비트코인 (변동성 큼)
    if "BTC" in symbol:
        if diff_pct >= 3.0: return "🚀 떡상"
        if diff_pct <= -3.0: return "📉 떡락"
        return "Wait"

    # 8. 주식 지수 (국장, 미장 공통)
    if symbol in ["^GSPC", "^IXIC", "^RUT", "^SOX", "^KS11", "^KQ11"]:
        if diff_pct >= 1.0: return "🔥 급등"
        if diff_pct <= -1.0: return "💧 급락"
        return "Normal"

    # 9. 기타 통화 (유로, 엔, 위안) & 원자재
    # - 통화는 0.5% 이상, 원자재는 1.5% 이상 변동 시 주목
    if "EUR" in symbol or "JPY" in symbol or "CNY" in symbol:
        if abs(diff_pct) > 0.5: return "🌊 변동"
    if symbol in ["GC=F", "SI=F", "HG=F"]:
        if abs(diff_pct) > 1.5: return "🌊 변동"

    return "-"

# ---------------------------------------------------------
# 🌞 아침용: 글로벌 매크로 & 미국 장 마감
# ---------------------------------------------------------
def get_morning_report(today_str):
    # 딕셔너리 리스트로 순서 유지 및 섹션 관리
    sections = [
        {
            "title": "💱 글로벌 환율 (Currency)",
            "tickers": {
                "🇺🇸 달러 인덱스": "DX-Y.NYB",
                "🇰🇷 환율 (USD)": "KRW=X",
                "🇪🇺 유로 (EUR)": "EURKRW=X",
                "🇯🇵 엔화 (JPY100)": "JPYKRW=X", 
                "🇨🇳 위안 (CNY)": "CNYKRW=X"
            }
        },
        {
            "title": "📊 금리 & 원자재 (Macro)",
            "tickers": {
                "🇺🇸 국채 10년물": "^TNX",
                "🇺🇸 국채 2년물(ETF)": "SHY", # SHY는 가격 기반(금리와 반대)
                "🇺🇸 하이일드 (HYG)": "HYG",
                "🛢️ 유가 (WTI)": "CL=F",
                "🥇 금 (Gold)": "GC=F",
                "🥉 구리 (Copper)": "HG=F",
                "🪙 코인 (BTC)": "BTC-USD"
            }
        },
        {
            "title": "🇺🇸 미국 증시 (Overnight)",
            "tickers": {
                "🇺🇸 S&P 500": "^GSPC",
                "🇺🇸 나스닥": "^IXIC",
                "🇺🇸 러셀 2000": "^RUT",
                "⚙️ 필라반도체": "^SOX",
                "😱 공포지수": "^VIX"
            }
        }
    ]

    msg = "```markdown\n"
    msg += f"# 📅 {today_str} 글로벌 모닝 브리핑\n\n"
    msg += f"## 1. 국내 주요 지수 - Morning\n\n"
    
    print("🌞 아침 리포트 생성 중...")

    for section in sections:
        msg += f"### {section['title']}\n"
        msg += "| 지표 | 현재가 | 전일비 | 상태 (Signal) |\n"
        msg += "| :--- | :--- | :--- | :--- |\n"

        for name, symbol in section['tickers'].items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                if len(hist) < 2: continue
                
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                
                # 1. 가격 포맷팅
                if "DX-Y" in symbol: price = f"{curr:.2f}"
                elif symbol == "^TNX": price = f"{curr:.2f}%"
                elif symbol == "SHY": price = f"${curr:.2f}" # ETF 가격임
                elif "JPY" in symbol: price = f"{curr*100:,.2f}원" # 100엔 환산
                elif "KRW" in symbol: price = f"{curr:,.2f}원" # 나머지 원화
                else: price = f"{curr:,.2f}" # 일반 달러/포인트
                
                # 2. 아이콘
                if diff_pct > 0: icon = "🔺"
                elif diff_pct < 0: icon = "🔻"
                else: icon = "➖"
                
                # 3. 시그널 로직 호출
                # SHY(2년물 대체)는 가격이 떨어지면 금리 상승이므로 로직 반대
                if symbol == "SHY":
                    if diff_pct < -0.1: sig = "금리 상승"
                    elif diff_pct > 0.1: sig = "금리 하락"
                    else: sig = "-"
                else:
                    sig = get_signal(symbol, curr, diff_pct)

                msg += f"| **{name}** | {price} | {icon} {abs(diff_pct):.2f}% | {sig} |\n"
            except: continue
        msg += "\n"

    msg += "```"
    send_telegram_message(msg)

# ---------------------------------------------------------
# 🌙 오후용: 국내장 마감 브리핑
# ---------------------------------------------------------
def get_closing_report(today_str):
    tickers = {
        "🇰🇷 코스피": "^KS11",
        "🇰🇷 코스닥": "^KQ11",
        "🇰🇷 환율 (마감)": "KRW=X"
    }
    
    msg = "```markdown\n"
    msg += f"# 🇰🇷 {today_str} 국내증시 마감\n\n"
    msg += "## 📉 2. 국내 시장 마감 요약\n"
    msg += "| 지표 | 현재가 | 전일비 | 상태 (Signal) |\n"
    msg += "| :--- | :--- | :--- | :--- |\n"
    
    print("🌙 마감 리포트 생성 중...")
    
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if len(hist) < 2: continue
            
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            diff_pct = ((curr - prev) / prev) * 100
            
            # 가격 포맷팅
            if "KRW" in symbol: price = f"{curr:,.0f}원"
            else: price = f"{curr:,.2f}"
            
            # 아이콘
            if diff_pct > 0: icon = "🔺"
            elif diff_pct < 0: icon = "🔻"
            else: icon = "➖"
            
            # 시그널 호출
            sig = get_signal(symbol, curr, diff_pct)

            msg += f"| **{name}** | {price} | {icon} {abs(diff_pct):.2f}% | {sig} |\n"
        except: continue
        
    msg += "\n### 📝 장 마감 메모\n"
    msg += "- **주도 섹터:** \n"
    msg += "- **외국인 수급:** \n"
    msg += "```"
    send_telegram_message(msg)

# ---------------------------------------------------------
# 🚀 메인 실행 로직
# ---------------------------------------------------------
if __name__ == "__main__":
    now_utc = datetime.utcnow()
    now_kst = now_utc + timedelta(hours=9)
    today_str = now_kst.strftime("%Y-%m-%d")
    current_hour = now_kst.hour

    print(f"🕒 현재 시간(KST): {current_hour}시")

    # 오후 3시(15시) 이후 실행 -> 마감 리포트
    if current_hour >= 15:
        get_closing_report(today_str)
    # 그 외(아침) -> 글로벌 모닝 브리핑
    else:
        get_morning_report(today_str)