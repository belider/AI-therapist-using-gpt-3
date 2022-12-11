# https://api.telegram.org/bot5680490866:AAGtDiCS_uH27_SEezh-iWLbY4afob_-dog/sendMessage?chat_id=288939647&text=Hello%20World!

# Поднять flask server, который слушает запросы.
# Передавать callback url в Capusta

# Когда приходит запрос
# Если статус платежа successs: 
#     устанавливать статус платежа в payments как success
#     писать сообщение success
#     устанавливать новый лимит сообщений

# Если статус платежа error
#     устанавливать статус платежа в payments как error
#     писать сообщение error


from flask import Flask, request, jsonify
import os
from database_class import Database
import requests


app = Flask(__name__)
db = Database()

PORT = int(os.environ.get('PORT', 8080))
HOST = "0.0.0.0"
BOT_TOKEN = os.getenv('BOT_TOKEN')

def send_message_in_bot(user_id, text): 
    response = requests.post(
        url=f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data={'chat_id': user_id, 'text': text}
    ).json()
    return response

@app.route('/', methods=['GET'])
def test_url(): 
    return "Hello world"

@app.route('/pmt', methods=['POST'])
def payment_callback_listener():
    data = request.get_json()
    print(data)

    payment_status = data['status']
    payment_id = data['id']

    # update payment status
    query = f"""UPDATE payments 
                SET status = '{payment_status}'
                WHERE payment_id='{payment_id}'; """
    db.execute_insert_query(query)
    
    user_id = data['custom']['user_id']

    # TODO send user message - success or error
    if payment_status == 'SUCCESS': 
        message = f'payment {payment_id} successfull'
        # TODO update user_paid_limit
    elif payment_status == 'FAIL': 
        message = f'payment {payment_id} error'
    
    print(message)
    send_message_in_bot(user_id, message)

    return "OK"

# test curl:
# curl -X POST http://192.168.1.102:8080/pmt -H "Content-Type: application/json" -d '{"Id": 79, "status": 3}'
# curl -X POST https://worker-production-9383.up.railway.app/pmt -H "Content-Type: application/json" -d '{"Id": 79, "status": 3}'

if __name__ == '__main__':
    app.run(
        host=HOST,
        port=PORT,
        debug=True
    )