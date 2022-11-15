import openai
import os
from telegram.ext import *
# import keys

# openai.api_key = keys.openai_api_key
# bot_token = keys.bot_token

os.getenv('OPENAI_API_KEY')
os.getenv('BOT_TOKEN')

print('starting up bot...')

def start_command(update, context):
    update.message.reply_text('Привет, меня зовут Софи.\nМеня обучили принципам когнитивно-поведенческой терапии. Я постараюсь помочь тебе справиться с тревогой и сложными состояниями.\nКак ты себя чувствуешь сейчас?')

def handle_response(text: str) -> str: 
    prompt = f'Ниже приводится беседа с когнитивно-поведенческим терапевтом. Терапевт поддерживает, сопереживает и дружелюбен.\n\nЯ: {text}\nТерапевт:'

    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=prompt,
        max_tokens = 2048,
        temperature=0.3,
        stream=False
        )
    return response.choices[0].text

def handle_message(update, context):
    message_type = update.message.chat.type
    text = str(update.message.text).strip() 
    user_id = update.message.chat.id

    print(f'User {user_id} says "{text}" in {message_type}')

    response = handle_response(text)
    update.message.reply_text(response)

def error(update, context): 
    print(f'Update: {update}\nCaused error: {context.error}')
 
if __name__ == '__main__':
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    
    #commands
    dp.add_handler(CommandHandler('start', start_command))

    #messages
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    
    #error
    dp.add_error_handler(error)

    #run bot
    updater.start_polling(1.0)
    updater.idle()