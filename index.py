from flask import Flask, request, jsonify
import requests
import uuid
import os
import urllib3

# Отключаем предупреждения о сертификатах Минцифры на зарубежном сервере Vercel
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

AUTH_KEY = os.environ.get("GIGACHAT_AUTH_KEY")

def get_access_token():
    url = "https://sberbank.ru"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {AUTH_KEY}'
    }
    payload = {'scope': 'GIGACHAT_API_PERS'}
    resp = requests.post(url, headers=headers, data=payload, verify=False, timeout=2.5)
    return resp.json().get('access_token')

@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    user_text = data.get('request', {}).get('original_utterance', '')

    # Приветствие при запуске навыка
    if data.get('session', {}).get('new', False) and not user_text:
        return jsonify({
            "version": data['version'],
            "response": {
                "text": "Привет! ГигаЧат на связи. О чем поговорим?",
                "end_session": False
            }
        })

    # Выход из навыка
    if user_text.lower() in ['хватит', 'выход', 'стоп', 'пока']:
        return jsonify({
            "version": data['version'],
            "response": {
                "text": "До связи!",
                "end_session": True
            }
        })

    try:
        token = get_access_token()
        chat_url = "https://sberbank.ru"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        payload = {
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": "Ты голосовой помощник. Отвечай кратко, по сути, без списков и сложного форматирования, максимум 2-3 предложения."},
                {"role": "user", "content": user_text}
            ]
        }
        resp = requests.post(chat_url, headers=headers, json=payload, verify=False, timeout=3.0)
        result = resp.json()
        answer = result['choices']['message']['content']
    except Exception:
        answer = "Не удалось получить ответ вовремя. Попробуй задать вопрос покороче."

    return jsonify({
        "version": data['version'],
        "response": {
            "text": answer,
            "end_session": False
        }
    })
