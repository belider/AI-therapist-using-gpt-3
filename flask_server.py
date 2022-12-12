from flask import Flask, request, jsonify
import os
from database_class import Database
import requests
from waitress import serve

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
    payment_id = data['invoiceId']

    # update payment status
    query = f"""UPDATE payments 
                SET status='{payment_status}'
                WHERE payment_id='{payment_id}'; """
    db.execute_insert_query(query)
    
    user_id = data['custom']['user_id']

    if payment_status == 'SUCCESS': 
        log_message = f'payment {payment_id} successfull'
        user_message = """Оплата прошла успешна. 
Вы можете продолжить общение 😊\n
/newsession - команда, чтобы начать разговор"""
        
        # update user paid limit
        query = f"""UPDATE user_paid_limits 
                SET paid_messages = paid_messages + 500
                WHERE user_id='{user_id}'; """
        db.execute_insert_query(query)
    elif payment_status == 'FAIL': 
        log_message = f'payment {payment_id} error'
        user_message = "К сожалению оплата не прошла, деньги не списались. \nПопробуйте оплатить еще раз по той же ссылке. "
    
    print(log_message)
    send_message_in_bot(user_id, user_message)

    return "OK"

# test curl:
# curl -X POST http://192.168.1.102:8080/pmt -H "Content-Type: application/json" -d '{"Id": 79, "status": 3}'
# curl -X POST https://worker-production-9383.up.railway.app/pmt -H "Content-Type: application/json" -d '{"Id": 79, "status": 3}'

if __name__ == '__main__':
    # running in development env
    # app.run(
    #     host=HOST,
    #     port=PORT, 
    #     debug=True
    # )

    # running in production env
    serve(app, host=HOST, port=PORT)