import requests


TOKEN = "fill this"
CHAT_ID = 0

def notifyMeInTelegram():
    params = {
        "chat_id": CHAT_ID,
        "text": "Some one looking for opponent"
    }
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendmessage", params=params)
