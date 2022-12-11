import openai
import os
from datetime import datetime, timedelta
import psycopg2
from telegram.ext import *
from telegram import *
import time

from gpt_wrapper import *
from database_logic import *
from database_class import Database
from payment_callback_listener import *

import pymorphy2
morph = pymorphy2.MorphAnalyzer()
from googletrans import Translator
translator = Translator()

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

openai.api_key = os.getenv('OPENAI_API_KEY')
bot_token = os.getenv('BOT_TOKEN')
payment_provider_token = os.getenv('PROVIDER_TOKEN')

db = Database()

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

        response_text = "Меня зовут Софи. Как я могу к тебе обращаться?"
        query.message.reply_text(response_text)
    
        response_time_delta = datetime.now() - current_dt

        #saving reply message to DB
        insert_message_in_db(db, user_id, is_bot=True, message_text=response_text, message_timestamp=message_dt + response_time_delta)

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

def newsession_command(update, context):
    current_dt = datetime.now()
    message_dt = update.message.date
    user_id = update.message.chat.id

    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    # saving /newsession message to DB
    insert_message_in_db(db, user_id, is_bot=False, message_text=update.message.text.strip(), message_timestamp=update.message.date)

    user_name = get_username_by_userid(db, user_id)

    # constructing prompt
    prompt_starter = 'Ниже приводится беседа с когнитивно-поведенческим терапевтом.\n\n'
    prompt = prompt_starter + 'Терапевт: Привет, меня зовут Софи. Как я могу к тебе обращаться?\n' + f'Я: {user_name}\n\n' + 'Терапевт:'
    print(f'--> prompt: {prompt}')

    
    response_candidates_text = create_gpt_response(prompt, db, user_id)
    final_response_text = response_candidates_text[0]

    print(f'--> response_text: {final_response_text}')
    update.message.reply_text(final_response_text)

    response_time_delta = datetime.now() - current_dt

    #saving reply message to DB
    insert_message_in_db(db, user_id, is_bot=True, message_text=final_response_text, message_timestamp=message_dt + response_time_delta)


def handle_response(text: str, user_id, context) -> str: 
    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    # select all messages from the previous command
    messages_from_last_command = get_messages_from_last_user_command(db, user_id)

    # getting user name
    user_name = get_username_by_userid(db, user_id)
    
    prompt = construct_prompt_from_messages_history(messages_from_last_command, user_name)
    
    response_candidates_text = create_gpt_response(prompt, db, user_id)
    
    return get_not_repeating_not_empty_response(db, response_candidates_text, messages_from_last_command, user_id)

def handle_message(update, context):
    message_text = str(update.message.text).strip() 
    # message_text = translator.translate(message_text_ru, dest='en').text

    user_id = update.message.chat.id
    message_dt = update.message.date
    user_tg_nick = update.message.from_user.username
    user_tg_name = str(update.message.from_user.first_name) + ' ' + str(update.message.from_user.last_name)
    user_tg_name = user_tg_name.replace('None', '').strip()

    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    current_dt = datetime.now()
    last_user_message = get_last_user_message(db, user_id)

    print(f'User {user_id} says "{message_text}" <- at {message_dt}')
    # saving user message to DB
    insert_message_in_db(db, user_id, is_bot=False, message_text=message_text, message_timestamp=message_dt)

    # checking if this was a reply to Welcome message
    print("==> last_user_message: ", last_user_message)
    if last_user_message == '/start': 
        # then current message is the user's Name

        gender = get_gender_by_user_name(user_name=message_text, telegram_name=user_tg_name)
        print(f'user gender: {gender}')
        # saving user name and gender to DB
        set_or_update_username(db, user_id, message_text, user_tg_nick, user_tg_name, gender)

        if gender == 'femn': 
            response = f"Привет, {message_text}. Что бы ты хотела обсудить?"
        else: 
            # gender is 'masc', 'neut' or None
            response = f"Привет, {message_text}. Что бы ты хотел обсудить?"
        update.message.reply_text(response)
    
    (paid_limit, paid_limit_status) = get_paid_limit_and_status_by_user(db, user_id)
    if paid_limit_status == 'trial ended': 
        print('User messages limit has ended.')
        # send monetization message
        response = f"""_Сообщение от команды бота: _

Ваш бесплатный лимит на {paid_limit} сообщений истек. 

Мы стремились сделать Софи как можно более доступным и простым способом психологической поддержки. 
Однако, она использует дорогие модели искусственного интеллекта, чтобы ответы были максимально полезны. 

Если вы хотите продолжить, вы можете купить пакет на 500 сообщений за $4.99."""
        buttons = [[InlineKeyboardButton(text="Оплатить", url="https://anybodygo.com/", pay=True)]]
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(response, reply_markup=reply_markup, parse_mode='markdown')
    elif paid_limit_status == 'paid plan ended': 
        # send monetization message
        response = f"""_Сообщение от команды бота: _

Ваш лимит на {paid_limit} сообщений истек. 

Мы стремились сделать Софи как можно более доступным и простым способом психологической поддержки. 
Однако, она использует дорогие модели искусственного интеллекта, чтобы ответы были максимально полезны. 

Если вы хотите продолжить, вы можете купить еще один пакет на 500 сообщений за $4.99."""
        buttons = [[InlineKeyboardButton(text="Оплатить 399 RUB", url="https://capu.st/bill5eea560c-e12b")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        # context.bot.send_invoice(
        #     chat_id=user_id, 
        #     title="title", 
        #     description="description", 
        #     payload="5", 
        #     provider_token=payment_provider_token, 
        #     currency="RUB", 
        #     prices=[LabeledPrice("label_test", 35000)],
        #     allow_sending_without_reply=True, 
        #     reply_markup=reply_markup
        # )
        update.message.reply_text(response, reply_markup=reply_markup, parse_mode='markdown')
    else: 
        response = handle_response(message_text, user_id, context)
        update.message.reply_text(response)

    response_time_delta = datetime.now() - current_dt
    print(f'Response time: {response_time_delta}')
    
    #saving gpt response to DB
    insert_message_in_db(db, user_id, is_bot=True, message_text=response, message_timestamp=message_dt + response_time_delta)

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

    app.run(
        host=HOST,
        port=PORT,
        debug=True
    )