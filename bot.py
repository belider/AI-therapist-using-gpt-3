import openai
import os
from datetime import datetime, timedelta
import psycopg2
from telegram.ext import *
from telegram import *
import time
import requests
import re

from gpt_wrapper import *
from database_logic import *
from database_class import Database

import pymorphy2
morph = pymorphy2.MorphAnalyzer()
from googletrans import Translator
translator = Translator()
from translate import *

CAPUSTA_EMAIL = os.getenv('CAPUSTA_EMAIL')
CAPUSTA_PROJECT_CODE = os.getenv('CAPUSTA_PROJECT_CODE')
CAPUSTA_TOKEN = os.getenv('CAPUSTA_TOKEN')

openai.api_key = os.getenv('OPENAI_API_KEY')
bot_token = os.getenv('BOT_TOKEN')

db = Database()

def get_gender_by_user_name(user_name: str, telegram_name: str):
    name = user_name
    gender = morph.parse(name)[0].tag.gender
    if gender == None or gender == 'neut': 
       # translating a user_name
       name = translator.translate(name, dest='ru').text
       print(f'translated user name: {name}')
       gender =  morph.parse(name)[0].tag.gender
    if gender == None or gender == 'neut':
        # translating a telegram name
        name = telegram_name
        print(f'user tg name: {telegram_name}')
        name = translator.translate(name, dest='ru').text
        print(f'translated tg name: {name}')
        gender =  morph.parse(name)[0].tag.gender
        print(f'gender by translated tg name: {gender}')
    if gender == None or gender == 'neut':
        name_split = name.split(' ')
        for name_part in name_split: 
            g = morph.parse(name_part)[0].tag.gender
            print(f'gender by name part "{name_part}": {g}')
            if g == 'masc' or g == 'femn':
                gender = g
    return gender

print('starting up a bot...')     

def query_handler(update, context): 
    current_dt = datetime.now()
    query = update.callback_query
    update.callback_query.answer()
    
    user_id = query.message.chat.id
    message_dt = query.message.date
    
    if "continue1" in query.data: 
        response_text = """Как получить более релевантный ответ? 

💆‍♀️ Сформулируйте, в чем заключается проблема. 
Например: "Чувствую себя тревожно из-за..."
Софи будет задавать вопросы и поможет придти к решению. 

💭 Укажите цель разговора. 
Например: "Мне нужен совет с ..."
В этом случае Софи расскажет, что знает из статей и книг по психологии. 

/newsession - команда на случай, если диалог зайдет в тупик"""
        buttons = [[InlineKeyboardButton("✔️ Начать сессию", callback_data="start_session")]]
        reply_markup = InlineKeyboardMarkup(buttons)

        query.edit_message_text(response_text, reply_markup=reply_markup)
    elif "start_session" in query.data: 
        query.delete_message()
        time.sleep(0.5)

        response_text_ru = "Меня зовут Софи. Как я могу к вам обращаться?"
        response_text_eng = "My name is Sophie. How can I call you?"
        query.message.reply_text(response_text_ru)
    
        response_time_delta = datetime.now() - current_dt

        #saving eng reply message to DB
        insert_message_in_db(db, user_id, is_bot=True, message_text=response_text_eng, message_timestamp=message_dt + response_time_delta)
    elif "usd_pay" in query.data: 
        response_text_ru = """К сожалению бот сейчас не поддерживает формат оплаты в USD. \nНапишите @belonel, чтобы оплатить переводом или в крипте. """
        query.message.reply_text(response_text_ru)
        insert_analytics_event_to_db(db, user_id, event_name="payment_message_button_click", event_params={"button": "USD"})

def start_command(update, context):
    message_dt = update.message.date
    user_id = update.message.chat.id
    message_text = update.message.text.strip()

    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    # savin /start message to DB
    # msg_type = 0 -> user comand
    # msg_type = 1 -> bot answer
    insert_message_in_db(db, user_id, is_bot=False, message_text=message_text, message_timestamp=message_dt)
    
    reply_text = """Привет 👋
Софи - это бот на основе искусственного интеллекта. Она хороший психолог и собеседник. Иногда ее ответы смешат, иногда наводят на размышления. Попробуй написать свой запрос. 

Все сообщения конфиденциальны. Бот сохраняет их анонимно и использует только чтобы отвечать с учетом предыдущих сообщений. """

    buttons = [[InlineKeyboardButton("✔️ Продолжить", callback_data="continue1")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    update.message.reply_text(reply_text, reply_markup=reply_markup)

TRIAL_ENDED_RESPONSE = """_Сообщение от команды бота: _

Ваш бесплатный лимит на {paid_limit} сообщений истек. 

Мы стремились сделать Софи как можно более доступным и простым способом психологической поддержки. 
Однако, она использует дорогие модели искусственного интеллекта, чтобы ответы были максимально полезны. 

Если вы хотите продолжить, вы можете купить пакет на 500 сообщений за 399 руб."""

PAID_PERIOD_ENDED_RESPONSE = """_Сообщение от команды бота: _

Ваш лимит на {paid_limit} сообщений истек. 

Мы стремились сделать Софи как можно более доступным и простым способом психологической поддержки. 
Однако, она использует дорогие модели искусственного интеллекта, чтобы ответы были максимально полезны. 

Если вы хотите продолжить, вы можете купить еще один пакет на 500 сообщений за 399 руб."""

def get_payment_buttons(payment_link_ru, usd_pay_callback="usd_pay"): 
    return [
        [InlineKeyboardButton(text="Оплатить 399 RUB", url=payment_link_ru)], 
        [InlineKeyboardButton(text="Оплатить в USD", callback_data=usd_pay_callback)]
    ]

def newsession_command(update, context):
    current_dt = datetime.now()
    message_dt = update.message.date
    user_id = update.message.chat.id

    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    # saving /newsession message to DB
    insert_message_in_db(db, user_id, is_bot=False, message_text=update.message.text.strip(), message_timestamp=update.message.date)

    (user_name, user_gender) = get_username_and_gender_by_userid(db, user_id)

    (paid_limit, paid_limit_status) = get_paid_limit_and_status_by_user(db, user_id)

    if paid_limit_status == 'trial ended': 
        print('User messages limit has ended.')
        payment_link = create_payment_link(db, user_id, reason=paid_limit_status, amount=399, currency="RUB")
        # send monetization message
        response = TRIAL_ENDED_RESPONSE.format(paid_limit=paid_limit)
        buttons = get_payment_buttons(payment_link)
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(response, reply_markup=reply_markup, parse_mode='markdown')
        insert_analytics_event_to_db(db, user_id, event_name="payment_message_sent", event_params={"reason": "trial ended"})
    elif paid_limit_status == 'paid plan ended': 
        # send monetization message
        payment_link = create_payment_link(db, user_id, reason=paid_limit_status, amount=399, currency="RUB")
        response = PAID_PERIOD_ENDED_RESPONSE.format(paid_limit=paid_limit)
        buttons = get_payment_buttons(payment_link)
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(response, reply_markup=reply_markup, parse_mode='markdown')
        insert_analytics_event_to_db(db, user_id, event_name="payment_message_sent", event_params={"reason": "paid plan ended"})
    else: 
        # constructing prompt
        prompt_starter = 'The following is a conversation with a cognitive behavioral therapist.\n\n'
        prompt = prompt_starter + 'Therapist: Hello, my name is Sophie. How can I call you?\n' + f'Me: {user_name}\n\n' + 'Therapist:'
        print(f'--> prompt: {prompt}')

        response_candidates_text = create_gpt_response(prompt, db, user_id)
        response_eng = str(response_candidates_text[0])

        # response_ru = translator.translate(response_eng, dest='ru').text
        response_ru = translate_using_available_translator(text=response_eng, target_lang='ru')

        print(f'--> response_text: {response_ru}')
        update.message.reply_text(response_ru)

        response_time_delta = datetime.now() - current_dt

        #saving reply message to DB
        insert_message_in_db(db, user_id, is_bot=True, message_text=response_eng, message_timestamp=message_dt + response_time_delta)


def handle_response(text: str, user_id, context) -> str: 
    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    # select all messages from the previous command
    messages_from_last_command = get_messages_from_last_user_command(db, user_id)

    # getting user name
    (user_name, user_gender) = get_username_and_gender_by_userid(db, user_id)
    
    prompt = construct_prompt_from_messages_history(messages_from_last_command, user_name)
    
    response_candidates_text = create_gpt_response(prompt, db, user_id)
    
    return get_not_repeating_not_empty_response(db, response_candidates_text, messages_from_last_command, user_id)

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
        }
    }

    headers = {
        'Authorization': f'Bearer {CAPUSTA_EMAIL}:{CAPUSTA_TOKEN}',
    }

    response = requests.request("POST", url, json=payload, headers=headers).json()

    try:
        payment_link = response['payUrl']
        print(f'--> payment link created: {payment_link}')

        query = f""" INSERT INTO payments (user_id, amount, currency, status, payment_link, created_at, reason, is_test, payment_id) 
                            VALUES ({user_id}, 
                                    {amount}, 
                                    '{currency}', 
                                    '{response['status']}', 
                                    '{payment_link}', 
                                    TIMESTAMP '{response['created_at']}', 
                                    '{reason}', 
                                    {is_test},
                                    '{response['id']}' ) """
        db.execute_insert_query(query)
    except Exception as err: 
        print(err)
        print(f'--> Capusta response: {response}')
        payment_link = 'https://www.google.com/'
    return payment_link


def handle_message(update, context):
    message_text_ru = str(update.message.text).strip() 
    message_text_eng = translator.translate(message_text_ru, dest='en').text

    user_id = update.message.chat.id
    message_dt = update.message.date
    user_tg_nick = update.message.from_user.username
    user_tg_name = str(update.message.from_user.first_name) + ' ' + str(update.message.from_user.last_name)
    user_tg_name = user_tg_name.replace('None', '').strip()
    (user_name, user_gender) = get_username_and_gender_by_userid(db, user_id)

    (paid_limit, paid_limit_status) = get_paid_limit_and_status_by_user(db, user_id)

    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    current_dt = datetime.now()
    last_user_message = get_last_user_message(db, user_id)

    print(f'User {user_id} says "{message_text_eng}" <- at {message_dt}')
    # saving user message to DB
    insert_message_in_db(db, user_id, is_bot=False, message_text=message_text_eng, message_timestamp=message_dt)

    # checking if this was a reply to Welcome message
    print("==> last_user_message: ", last_user_message)
    if last_user_message == '/start': 
        # then current message is the user's Name

        gender = get_gender_by_user_name(user_name=message_text_ru, telegram_name=user_tg_name)
        print(f'user gender: {gender}')
        # saving user name and gender to DB
        set_or_update_username(db, user_id, message_text_ru, user_tg_nick, user_tg_name, gender)
        
        response = f"{message_text_ru}, очень приятно. Что бы вы хотели обсудить?"
        update.message.reply_text(response)
        
        response_eng = f"Hi, {message_text_ru}. What would you like to discuss?"
        response_time_delta = datetime.now() - current_dt
        insert_message_in_db(db, user_id, is_bot=True, message_text=response_eng, message_timestamp=message_dt + response_time_delta)
    elif paid_limit_status == 'trial ended': 
        print('User messages limit has ended.')
        payment_link = create_payment_link(db, user_id, reason=paid_limit_status, amount=399, currency="RUB")
        # send monetization message
        response = TRIAL_ENDED_RESPONSE.format(paid_limit=paid_limit)
        buttons = get_payment_buttons(payment_link)
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(response, reply_markup=reply_markup, parse_mode='markdown')
        insert_analytics_event_to_db(db, user_id, event_name="payment_message_sent", event_params={"reason": "trial ended"})
    elif paid_limit_status == 'paid plan ended': 
        # send monetization message
        payment_link = create_payment_link(db, user_id, reason=paid_limit_status, amount=399, currency="RUB")
        response = PAID_PERIOD_ENDED_RESPONSE.format(paid_limit=paid_limit)
        buttons = get_payment_buttons(payment_link)
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(response, reply_markup=reply_markup, parse_mode='markdown')
        insert_analytics_event_to_db(db, user_id, event_name="payment_message_sent", event_params={"reason": "paid plan ended"})
    else: 
        (response, lang) = handle_response(message_text_eng, user_id, context)
        
        if lang == 'rus': 
            response_ru = response
            response_eng = translator.translate(response, dest='en').text
        elif lang == 'eng': 
            response_eng = response
            # response_ru = translator.translate(response, dest='ru').text
            response_ru = translate_using_available_translator(text=response, target_lang='ru')

        update.message.reply_text(response_ru)
        
        response_time_delta = datetime.now() - current_dt
        print(f'Response time: {response_time_delta}')
        
        #saving gpt response to DB
        insert_message_in_db(db, user_id, is_bot=True, message_text=response_eng, message_timestamp=message_dt + response_time_delta)

def error(update, context): 
    print(f'Update: \n{update}\nCaused error: {context.error}')
    

if __name__ == '__main__':

    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    
    #commands
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('newsession', newsession_command))

    #messages
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    dp.add_handler(CallbackQueryHandler(query_handler))
    
    #error
    dp.add_error_handler(error)

    #run bot
    updater.start_polling(0.5)
    updater.idle()