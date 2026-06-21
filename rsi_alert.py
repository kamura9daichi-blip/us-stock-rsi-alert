import yfinance as yf
from ta.momentum import RSIIndicator
import requests

# ==========================
# SendGrid メール送信
# ==========================
def send_email(subject, body, to_email):
    api_key = "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"  # ←貼る
    sender = "kamura.9.daichi@gmail.com"  # ←SendGridで認証したメール

    data = {
        "personalizations": [
            {"to": [{"email": to_email}]}
        ],
        "from": {"email": sender},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}]
    }

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=data
    )

    print("送信結果:", response.status_code)


# ==========================
# 監視銘柄
# ==========================
stocks = {
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "GOOGL": "Google",
    "LLY": "LLY",
    "QQQ": "QQQ",
    "GEV": "GEV",
    "GE": "GE",
    "CRWD": "CRWD",
    "AVGO": "AVGO(ブロードコム)",
    "LRCX": "LRCX(ラムリサーチ)",
    "ANET": "ANET",
    "COST": "COST",
    "AU": "AU",
    "TOL": "TOL",
    "DELL": "DELL",
    "SCCO": "SCCO",
    "CIB": "CIB",
    "INTC": "INTC",
    "GLW": "GLW",
    "GS":"GS"
}

# ==========================
# メッセージ作成
# ==========================
message = "【米国株RSIアラート】\n\n"

for ticker, name in stocks.items():
    try:
        df = yf.download(
            ticker,
            period="1y",
            interval="1d",
            progress=False
        )

        if df.empty:
            continue

        close = df["Close"].squeeze()

        if len(close) < 20:
            continue

        current_price = float(close.iloc[-1])

        rsi_series = RSIIndicator(close).rsi().dropna()
        if rsi_series.empty:
            continue

        current_rsi = float(rsi_series.iloc[-1])

        percentile = (
            (rsi_series <= current_rsi).sum()
            / len(rsi_series)
        ) * 100

        if percentile <= 10:
            comment = "かなり売られています"
        elif percentile <= 30:
            comment = "売られ気味"
        elif percentile >= 90:
            comment = "かなり買われています"
        elif percentile >= 70:
            comment = "買われ気味"
        else:
            continue

        message += (
            f"{name} ({ticker})\n"
            f"現在価格 : ${current_price:.2f}\n"
            f"RSI : {current_rsi:.1f}\n"
            f"{comment}\n\n"
        )

    except Exception as e:
        print(f"{ticker} エラー: {e}")


# ==========================
# SendGrid で送信
# ==========================
if message != "【米国株RSIアラート】\n\n":
    send_email(
        subject="米国株 RSI アラート",
        body=message,
        to_email="kamura.9.daichi@gmail.com"  # ←ここに送信先
    )
    print("メール送信しました")
else:
    print("通知対象はありませんでした。")