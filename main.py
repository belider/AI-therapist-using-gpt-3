import openai
import os
from datetime import datetime, timedelta
import psycopg2
from telegram.ext import *
from telegram import ChatAction

from gpt_wrapper import *
from database_logic import *
from database_class import Database

openai.api_key = os.getenv('OPENAI_API_KEY')
bot_token = os.getenv('BOT_TOKEN')

db = Database()

print('starting up a bot...')     

def start_command(update, context):
    current_dt = datetime.now()
    message_dt = update.message.date
    user_id = update.message.chat.id
    message_text = update.message.text.strip()

    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    # savin /start message to DB
    # msg_type = 0 -> user comand
    # msg_type = 1 -> bot answer
    insert_message_in_db(db, user_id, is_bot=False, message_text=message_text, message_timestamp=message_dt)

    reply_text = 'Привет, меня зовут Софи.\nМеня обучили принципам когнитивно-поведенческой терапии. Я постараюсь помочь тебе справиться с тревогой и сложными состояниями.\nКак я могу к тебе обращаться?'
    update.message.reply_text(reply_text)

    response_time_delta = datetime.now() - current_dt

    #saving reply message to DB
    insert_message_in_db(db, user_id, is_bot=True, message_text=reply_text, message_timestamp=message_dt + response_time_delta)

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

    
    response_candidates_text = create_gpt_response(prompt)
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
    
    response_candidates_text = create_gpt_response(prompt)
    
    return get_not_repeating_not_empty_response(response_candidates_text, messages_from_last_command)

def handle_message(update, context):
    message_text = str(update.message.text).strip() 
    user_id = update.message.chat.id
    message_dt = update.message.date
    user_tg_nick = update.message.from_user.username

    # "Sofi is typing..." animation
    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    current_dt = datetime.now()

    print(f'User {user_id} says "{message_text}" <- at {message_dt}')

    # checking if this was a reply to /start message
    last_user_message = get_last_user_message(db, user_id)
    if last_user_message == '/start': 
        # then current message is the user's Name
        set_or_update_username(db, user_id, message_text, user_tg_nick)

    # saving user message to DB
    insert_message_in_db(db, user_id, is_bot=False, message_text=message_text, message_timestamp=message_dt)

    response = handle_response(message_text, user_id, context)

    response_time_delta = datetime.now() - current_dt
    print(f'GPT response time: {response_time_delta}')
    
    #saving gpt response to DB
    insert_message_in_db(db, user_id, is_bot=True, message_text=response, message_timestamp=message_dt + response_time_delta)

    update.message.reply_text(response)

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
    
    #error
    dp.add_error_handler(error)

    #run bot
    updater.start_polling(0.5)
    updater.idle()