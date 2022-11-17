import openai
import os
from datetime import datetime, timedelta
import psycopg2
from telegram.ext import *

openai.api_key = os.getenv('OPENAI_API_KEY')
bot_token = os.getenv('BOT_TOKEN')

print('connecting to database...')

db_name = os.getenv('PGDATABASE')
db_user = os.getenv('PGUSER')
db_pass = os.getenv('PGPASSWORD')
db_host = os.getenv('PGHOST')
db_port = os.getenv('PGPORT')

conn = psycopg2.connect(
   database=db_name, user=db_user, password=db_pass, host=db_host, port=db_port
)
cursor = conn.cursor()
cursor.execute("select version()")
# read a single row from query result using fetchone() method.
data = cursor.fetchone()
print("Connection established to: ",data)
#Closing the connection
# cursor.close()
# conn.close()

print('starting up bot...')

def messages_history_to_text_dialogue(messages): 
    dialogue = ''
    for msg in messages:
        if msg[3] in ['/start', '/newsession']: 
            # this is command message
            continue
        if msg[2]:
            # bot message
            dialogue += f'Терапевт: {msg[3]}\n'
        else:
            # user message
            dialogue += f'Я: {msg[3]}\n\n'
    print(dialogue)
    return dialogue
        

def start_command(update, context):
    current_dt = datetime.now()
    message_dt = update.message.date

    # savin /start message to DB
    # msg_type = 0 -> user comand
    # msg_type = 1 -> bot answer
    insert_query = f""" INSERT INTO messages (user_id, msg_type, msg_text, msg_dt) 
                        VALUES ({update.message.chat.id}, {bool(0)}, '{update.message.text.strip()}', TIMESTAMP '{message_dt}') """
    cursor.execute(insert_query)
    conn.commit()


    reply_text = 'Привет, меня зовут Софи.\nМеня обучили принципам когнитивно-поведенческой терапии. Я постараюсь помочь тебе справиться с тревогой и сложными состояниями.\nКак я могу к тебе обращаться?'
    update.message.reply_text(reply_text)

    response_time_delta = datetime.now() - current_dt

    #saving reply message to DB
    insert_query = f""" INSERT INTO messages (user_id, msg_type, msg_text, msg_dt) 
                        VALUES ({update.message.chat.id}, {bool(1)}, '{reply_text}', TIMESTAMP '{message_dt + response_time_delta}') """
    cursor.execute(insert_query)
    conn.commit()

def newsession_command(update, context):
    current_dt = datetime.now()
    message_dt = update.message.date
    user_id = update.message.chat.id

    # saving /newsession message to DB
    insert_query = f""" INSERT INTO messages (user_id, msg_type, msg_text, msg_dt) 
                        VALUES ({user_id}, {bool(0)}, '{update.message.text.strip()}', TIMESTAMP '{update.message.date}') """
    cursor.execute(insert_query)
    conn.commit()

    select_query = f"""select user_name from users where user_id = {user_id}"""        
    cursor.execute(select_query)
    name = cursor.fetchone()[0]

    prompt_starter = 'Ниже приводится беседа с когнитивно-поведенческим терапевтом.\n\n'
    prompt = prompt_starter + 'Терапевт: Привет, меня зовут Софи. Как я могу к тебе обращаться?\n' + f'Я: {name}\n\n' + 'Терапевт:'
    print(f'--> prompt: {prompt}')

    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=prompt,
        max_tokens = 2048,
        temperature=0.3,
        stream=False, 
        stop='\n'
        )
    response_text = response.choices[0].text
    print(f'--> response_text: {response_text}')
    update.message.reply_text(response_text)

    response_time_delta = datetime.now() - current_dt

    #saving reply message to DB
    insert_query = f""" INSERT INTO messages (user_id, msg_type, msg_text, msg_dt) 
                        VALUES ({update.message.chat.id}, {bool(1)}, '{response_text}', TIMESTAMP '{message_dt + response_time_delta}') """
    cursor.execute(insert_query)
    conn.commit()

    

def handle_response(text: str, user_id) -> str: 
    # select all messages from the previous command like /%
    select_query = f"""select *
                        from messages m
                        join (select user_id, 
                                        max(msg_id) last_command 
                                from messages 
                                where msg_text like '/%' group by user_id
                        ) lm on lm.user_id = m.user_id 
                            and m.msg_id >= lm.last_command 
                        where m.user_id = {user_id}
                        order by msg_id
                        """
    cursor.execute(select_query)
    messages_from_last_command = cursor.fetchall()
    # print(messages_from_last_command, '\n')
    last_command = messages_from_last_command[0][3]

    prompt_starter = 'Ниже приводится беседа с когнитивно-поведенческим терапевтом.\n\n'
    dialogue_from_last_comand = messages_history_to_text_dialogue(messages_from_last_command)

    if last_command == '/start':
        prompt = ''
        print('last command was /start')
        prompt = prompt_starter + dialogue_from_last_comand + 'Терапевт:'
    elif last_command == '/newsession':
        select_query = f"""select user_name from users where user_id = {user_id}"""        
        cursor.execute(select_query)
        name = cursor.fetchone()[0]
        print('last command was /newsession')
        print(f'user name: {name}')
        prompt = prompt_starter + 'Терапевт: Привет, меня зовут Софи. Как я могу к тебе обращаться?\n' + f'Я: {name}\n\n' + dialogue_from_last_comand + 'Терапевт:'
    
    print(f'--> prompt: {prompt}')

    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=prompt,
        max_tokens = 2048,
        temperature=0.3,
        stream=False, 
        stop='\n'
        )
    return response.choices[0].text

def handle_message(update, context):
    text = str(update.message.text).strip() 
    user_id = update.message.chat.id
    message_dt = update.message.date
    user_tg_nick = update.message.from_user.username

    current_dt = datetime.now()

    print(f'User {user_id} says "{text}" <- at {message_dt}')

    # checking if this was a reply to /start message
    select_query = f"""SELECT msg_text from messages where user_id={user_id} and msg_type = false order by msg_dt desc limit 1"""
    cursor.execute(select_query)
    last_user_message = cursor.fetchall()[0]

    if str(last_user_message[0]) == '/start': 
        # then current message is the user's Name
        # saving name to DB
        query = f"""UPDATE users SET user_id={user_id}, user_name='{text}', tg_nick='{user_tg_nick}' WHERE user_id={user_id};
                    INSERT INTO users (user_id, user_name, tg_nick)
                        SELECT {user_id}, '{text}', '{user_tg_nick}'
                        WHERE NOT EXISTS (SELECT 1 FROM users WHERE user_id={user_id});"""
        cursor.execute(query)
        conn.commit()
        print(f"name {text} inserted in users DB")

    # saving user message to DB
    insert_query = f"""INSERT INTO messages (user_id, msg_type, msg_text, msg_dt) 
                        VALUES ({user_id}, {bool(0)}, '{text}', TIMESTAMP '{message_dt}');"""
    cursor.execute(insert_query)
    conn.commit()
    print(f'message {text} inserted in messages DB\n')

    response = handle_response(text, user_id)
    print(f'--> response: {response}')
    response_time_delta = datetime.now() - current_dt
    print(f'GPT response time: {response_time_delta}')
    
    #saving gpt response to DB
    insert_query = f""" INSERT INTO messages (user_id, msg_type, msg_text, msg_dt) 
                        VALUES ({user_id}, {bool(1)}, '{response}', TIMESTAMP '{message_dt + response_time_delta}');"""
    print(f'message "{response}" inserted in DB')
    cursor.execute(insert_query)
    conn.commit()

    update.message.reply_text(response)

def error(update, context): 
    print(f'Update: {update}\nCaused error: {context.error}')
 
if __name__ == '__main__':
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    
    #commands
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('newsession', newsession_command))

    #messages
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    
    #error
    dp.add_error_handler(error)

    #run bot
    updater.start_polling(0.5)
    updater.idle()