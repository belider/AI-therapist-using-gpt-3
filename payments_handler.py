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
import requests

CAPUSTA_EMAIL = os.getenv('CAPUSTA_EMAIL')
CAPUSTA_PROJECT_CODE = os.getenv('CAPUSTA_PROJECT_CODE')
CAPUSTA_TOKEN = os.getenv('CAPUSTA_TOKEN')


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

    # TODO update_payment_type
    # TODO update user_paid_limit
    # TODO send user message - success or error

    return "success"

# test curl:
# curl -X POST http://192.168.1.102:8080/pmt -H "Content-Type: application/json" -d '{"Id": 79, "status": 3}'
# curl -X POST https://worker-production-9383.up.railway.app/pmt -H "Content-Type: application/json" -d '{"Id": 79, "status": 3}'

def create_payment_link(db, user_id, reason, amount, currency) -> str: 
    is_test = True
    url = 'https://api.capusta.space/v1/partner/payment'
    # bill_id = '5eea560c-e12b'
    
    payload = {
        'projectCode': CAPUSTA_PROJECT_CODE,
        'amount': {
            'currency': currency,
            'amount': amount*100
        },
        'description': '500 сообщений для AI therapist bot', 
        "custom": {
                "user_id": user_id
        },
        "test": is_test
    }

    headers = {
        'Authorization': f'Bearer {CAPUSTA_EMAIL}:{CAPUSTA_TOKEN}',
    }

    response = requests.request("POST", url, json=payload, headers=headers).json()
    
    payment_link = response['payUrl']
    print(f'--> payment link created: {payment_link}')

    query = f""" INSERT INTO payments (user_id, amount, currency, status, payment_link, created_at, reason, is_test) 
                        VALUES ({user_id}, 
                                {amount}, 
                                '{currency}', 
                                '{response['status']}', 
                                '{payment_link}', 
                                TIMESTAMP '{response['created_at']}', 
                                '{reason}', 
                                {is_test}) """
    db.execute_insert_query(query)
    
    return payment_link