import yfinance as yf
from ta.momentum import RSIIndicator
import os
import json
import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# ==========================
# Secrets から credentials.json を復元
# ==========================
def restore_credentials_json():
    cred_str = os.getenv("GMAIL_CREDENTIALS_JSON")
    if cred_str:
        with open("credentials.json", "w") as f:
            f.write(cred_str)

restore_credentials_json()

# ==========================
# Secrets から token.json を復元
# ==========================
def restore_token_json():
    token_str = os.getenv("GMAIL_TOKEN_JSON")
    if token_str:
        with open("token.json", "w") as f:
            f.write(token_str)

restore_token_json()

# ==========================
# Gmail API 認証
# ==========================
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def gmail_service():
    creds = None

    # Secrets から復元された token.json を使う
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        return build("gmail", "v1", credentials=creds)

    # ここから下はローカル専用（GitHub Actions では絶対に使わない）
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ==========================
# Gmail API メール送信
# ==========================
def send_email(subject, body, to_email):
    service = gmail_service()

    message = MIMEText(body)
    message["to"] = to_email
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {"raw": raw}

    sent = service.users().messages().send(
        userId="me",
        body=message_body
    ).execute()

    print("送信完了:", sent.get("id"))

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
    "GS": "GS",
    "JNJ": "JNJ",
    "SMH": "SMH",
    "CPA": "CPA",
    "MPC": "MPC",
    "HONA": "HONA",
    "CAT": "CAT",
    "AAPL": "Apple",
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
# Gmail API で送信
# ==========================
if message != "【米国株RSIアラート】\n\n":
    send_email(
        subject="米国株 RSI アラート",
        body=message,
        to_email=os.getenv("GMAIL_TO")   # ← Secrets から取得
    )
    print("メール送信しました")
else:
    print("通知対象はありませんでした。")
