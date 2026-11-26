from flask import Flask, request, jsonify
import requests
import uuid
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

AUTH_KEY = os.environ.get("GIGACHAT_AUTH_KEY", "").strip()

def get_access_token():
    url = "https://sberbank.ru"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {AUTH_KEY}'
    }
    payload = {'scope': 'GIGACHAT_API_PERS'}
    resp = requests.post(url, headers=headers, data=payload, verify=False, timeout=4.0)
    return resp.json().get('access_token')

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def webhook(path):
    if request.method == 'GET':
        return "Server is working!", 200

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "No JSON"}), 200

    user_text = data.get('request', {}).get('original_utterance', '')
    version = data.get('version', '1.0')

    if data.get('session', {}).get('new', False) and not user_text:
        return jsonify({
            "version": version,
            "response": {
                "text": "Привет! ГигаЧат на связи. О чем поговорим?",
                "end_session": False
            }
        })

    if user_text.lower() in ['хватит', 'выход', 'стоп', 'пока']:
        return jsonify({
            "version": version,
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
        resp = requests.post(chat_url, headers=headers, json=payload, verify=False, timeout=4.0)
        result = resp.json()
        answer = result['choices']['message']['content']
    except Exception as e:
        answer =  answer = f"Детали: {str(e)}"

    return jsonify({
        "version": version,
        "response": {
            "text": answer,
            "end_session": False
        }
    })
