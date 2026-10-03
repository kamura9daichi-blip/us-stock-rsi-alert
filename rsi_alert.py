import yfinance as yf
from ta.momentum import RSIIndicator
import os
import resend

# ==========================
# Resend API キー設定
# ==========================
resend.api_key = os.getenv("RESEND_API_KEY")

# ==========================
# Resend メール送信
# ==========================
def send_email(subject, body, to_email):
    params = {
        "from": "RSI Alert <onboarding@resend.dev>",  # 認証済みドメインに変更可
        "to": [to_email],
        "subject": subject,
        "html": body.replace("\n", "<br>")  # 改行をHTMLに変換
    }

    try:
        email = resend.Emails.send(params)
        print("送信完了:", email)
    except Exception as e:
        print("送信エラー:", e)


# ==========================
# 監視銘柄
# ==========================
stocks = {
    "VOO": "VOO",
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
    "MU": "MU",
    "COST": "COST",
    "AU": "AU",
    "TOL": "TOL",
    "DELL": "DELL",
    "SCCO": "SCCO",
    "CIB": "CIB",
    "INTC": "INTC",
    "GLW": "GLW",
    "GS": "GS",
    "JPM": "JPM",
    "JNJ": "JNJ",
    "SMH": "SMH",
    "CPA": "CPA",
    "MPC": "MPC",
    "HONA": "HONA",
    "CAT": "CAT",
    "AAPL": "Apple",
    "CVX": "CVX",
    "FDX": "FDX",
    "US10Y": "US10Y",
    "DAL": "DAL",
    "PLTR": "PLTR",
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
        elif percentile <= 20:
            comment = "売られ気味"
        elif percentile >= 90:
            comment = "かなり買われています"
        elif percentile >= 80:
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
# Resend で送信
# ==========================
if message != "【米国株RSIアラート】\n\n":
    send_email(
        subject="米国株 RSI アラート",
        body=message,
        to_email=os.getenv("RESEND_TO")   # ← Secrets から取得
    )
    print("メール送信しました")
else:
    print("通知対象はありませんでした。")

