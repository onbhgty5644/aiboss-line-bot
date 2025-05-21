import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# ตั้งค่าจาก Environment Variables หรือกำหนดตรงนี้ก็ได้ (สำหรับทดสอบ)
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running."

@app.route("/callback", methods=['POST'])
def callback():
    # รับ signature เพื่อยืนยันว่ามาจาก LINE จริง
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ฟังก์ชันตอบกลับเมื่อผู้ใช้ส่งข้อความ
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    reply = f"คุณกิน: {text} (เดี๋ยวเราจะคำนวณแคลให้ในอนาคตนะ!)"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(port=5000)
