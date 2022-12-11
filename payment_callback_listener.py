# https://api.telegram.org/bot5680490866:AAGtDiCS_uH27_SEezh-iWLbY4afob_-dog/sendMessage?chat_id=288939647&text=Hello%20World!

# Поднять flask server, который слушает запросы.
# Передавать callback url в Capusta

# Когда приходит запрос
# Если статус платежа successs: 
#     устанавливать статус платежа в payments как success
#     писать сообщение success
#     устанавливать новый лимит сообщений

# Если статус платежа error
#     устанавливать статус платежа в payments как success
#     писать сообщение error


from flask import Flask, request, jsonify
import os

app = Flask(__name__)

PORT = int(os.environ.get('PORT', 8080))
HOST = "0.0.0.0"

@app.route('/', methods=['GET'])
def test_url(): 
    return "Hello world"

@app.route('/pmt', methods=['POST'])
def payment_callback_listener():
    data = request.get_json()
    print(data)
    return "success"

# test curl:
# curl -X POST http://192.168.1.102:8080/pmt -H "Content-Type: application/json" -d '{"Id": 79, "status": 3}'
# curl -X POST https://worker-production-9383.up.railway.app/pmt -H "Content-Type: application/json" -d '{"Id": 79, "status": 3}'