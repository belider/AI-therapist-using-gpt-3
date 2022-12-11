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


app = Flask(__name__)
db = Database()

PORT = int(os.environ.get('PORT', 8080))
HOST = "0.0.0.0"

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
    
    # TODO send user message - success or error
    if payment_status == 'SUCCESS': 
        print(f'payment {payment_id} successfull')
        # TODO update user_paid_limit
    elif payment_status == 'FAIL': 
        print(f'payment {payment_id} error')

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