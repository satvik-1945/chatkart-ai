import os
import requests
from flask import Flask, request

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN", "chatkart-verify")
RASA_URL = os.environ.get("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")

@app.route("/", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return challenge, 200
    else:
        return "Verification token mismatch", 403

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"Incoming webhook: {data}")

    if "entry" in data:
        for entry in data["entry"]:
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text")

                    if message_text:
                        send_to_rasa(sender_id, message_text)
    return "EVENT_RECEIVED", 200

def send_to_rasa(sender_id, text):
    payload = {"sender": sender_id, "message": text}
    response = requests.post(RASA_URL, json=payload)
    
    if response.status_code == 200:
        responses = response.json()
        for r in responses:
            if "text" in r:
                send_to_facebook(sender_id, r["text"])

def send_to_facebook(recipient_id, message_text):
    url = "https://graph.facebook.com/v17.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, params=params, json=payload, headers=headers)
    print(f"FB Send Response: {response.status_code}, {response.text}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007)    