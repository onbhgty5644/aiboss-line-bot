import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
NUTRITIONIX_APP_ID = os.getenv('NUTRITIONIX_APP_ID')
NUTRITIONIX_APP_KEY = os.getenv('NUTRITIONIX_APP_KEY')

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running."

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text

    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_APP_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "query": user_input,
        "timezone": "Asia/Bangkok"
    }

    try:
        response = requests.post(
            "https://trackapi.nutritionix.com/v2/natural/nutrients",
            json=data,
            headers=headers
        )
        result = response.json()

        if 'foods' in result:
            message_lines = ["ข้อมูลโภชนาการสำหรับ:"]
            total_calories = 0
            total_fat = 0
            total_protein = 0
            total_carbs = 0

            for food in result['foods']:
                name = food.get('food_name', 'ไม่ระบุชื่ออาหาร').capitalize()
                qty = food.get('serving_qty', 0)
                unit = food.get('serving_unit', '')
                weight = food.get('serving_weight_grams', 0)

                cal = food.get('nf_calories', 0)
                fat = food.get('nf_total_fat', 0)
                protein = food.get('nf_protein', 0)
                carbs = food.get('nf_total_carbohydrate', 0)

                total_calories += cal
                total_fat += fat
                total_protein += protein
                total_carbs += carbs

                # ข้อความรายละเอียดอาหาร
                line = f"\n{qty} {unit} {name} (ประมาณ {weight:.0f} กรัม) มี"
                line += f"\n- พลังงาน: {cal:.0f} kcal"
                line += f"\n- ไขมัน: {fat:.1f} กรัม"
                line += f"\n- โปรตีน: {protein:.1f} กรัม"
                line += f"\n- คาร์โบไฮเดรต: {carbs:.1f} กรัม"

                message_lines.append(line)

            message_lines.append("\nรวมทั้งหมด (โดยประมาณ):")
            message_lines.append(f"- พลังงาน: {total_calories:.0f} kcal")
            message_lines.append(f"- ไขมัน: {total_fat:.1f} กรัม")
            message_lines.append(f"- โปรตีน: {total_protein:.1f} กรัม")
            message_lines.append(f"- คาร์โบไฮเดรต: {total_carbs:.1f} กรัม")

            reply_text = "\n".join(message_lines)

        else:
            reply_text = "ขออภัย ไม่สามารถวิเคราะห์ข้อมูลได้ กรุณาลองใหม่อีกครั้ง"

    except Exception as e:
        reply_text = f"เกิดข้อผิดพลาด: {str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000)
