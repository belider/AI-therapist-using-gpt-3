import openai
import sys
from database_logic import *
from datetime import datetime
import random

def create_gpt_response(prompt, db, user_id):
    response_candidates_text = []
    try: 
        response = openai.Completion.create(
            # model="text-davinci-003",
            model="text-curie-001", 
            prompt=prompt,
            max_tokens = 1000,
            n = 1,
            temperature=0.5,
            stop="Я: "
            )
        #calculating request cost
        total_tokens = response["usage"]["total_tokens"]
        if "davinci" in response["model"]: 
            cost = total_tokens * 0.02 / 1000
        elif "curie" in response["model"]: 
            cost = total_tokens * 0.002 / 1000
        # saving request info
        # TODO add request_dt
        insert_gpt_request_to_db(db, request_id=response["id"], user_id=user_id, request_dt=datetime.now(), prompt_text=prompt, completion_text=response["choices"][0].text, total_tokens=total_tokens, model=response["model"], cost=cost)

        for i in range(len(response["choices"])):
            response_candidates_text.append(response.choices[i].text)

    except Exception as err:
        print(err)
        # get details about the exception
        err_type, err_obj, traceback = sys.exc_info()

        # get the line number when exception occured
        line_num = traceback.tb_lineno
        # print the error
        print ("\nERROR while making request to GPT:", err, "on line number:", line_num)
        print ("openai traceback:", traceback, "-- type:", err_type)

        response_candidates_text = ["Сообщение от команды бота: \nИзвините, Софи сейчас перегружена. \nПопробуйте написать снова чуть позже"]
    
    return response_candidates_text

def messages_history_to_text_dialogue(messages, max_dialogue_len=2000, max_messages_len=4): 
    dialogue = ''
    for index, msg in enumerate(reversed(messages), start=1):
        if msg[3] in ['/start', '/newsession']: 
            # this is command message
            continue
        if len(dialogue) > max_dialogue_len or index > max_messages_len: 
            return dialogue
        if msg[2]:
            # bot message
            dialogue = f'Терапевт: {msg[3]}\n' + dialogue
        else:
            # user message
            dialogue = f'Я: {msg[3]}\n\n' + dialogue
    return dialogue

def construct_prompt_from_messages_history(messages_from_last_command, user_name):
    last_command = messages_from_last_command[0][3]

    prompt_starter = 'Ниже приводится беседа с когнитивно-поведенческим терапевтом.\n\n'
    dialogue_from_last_comand = messages_history_to_text_dialogue(messages_from_last_command)

    prompt = '' 
    if last_command == '/start':
        print('last command was /start')
        prompt = prompt_starter + dialogue_from_last_comand + 'Терапевт:'
    elif last_command == '/newsession':
        print('last command was /newsession')
        print(f'user name: {user_name}')
        prompt = prompt_starter + 'Терапевт: Привет, меня зовут Софи. Как я могу к тебе обращаться?\n' + f'Я: {user_name}\n\n' + dialogue_from_last_comand + 'Терапевт:'
    
    print(f'--> prompt: {prompt}')
    return prompt

def get_not_repeating_not_empty_response(db, response_candidates, messages_history, user_id):
    user_name = get_username_by_userid(db, user_id)
    
    # getting gpt responses from dialogue
    last_gpt_messages = []
    for el in messages_history: 
        if el[2] == True:
            last_gpt_messages.append(el[3].strip().lower())
    
    print(f'----> last gpt messages: {last_gpt_messages}\n')
    
    response_candidates_number = len(response_candidates)

    response_candidates_lower_case = []
    for i in range(response_candidates_number):
        response_candidates_lower_case.append(response_candidates[i].lower().strip())
        print(f'-----> response[{i}]: {response_candidates_lower_case[i]}')
    
    final_response_text = response_candidates_lower_case[0]

    for message_item in last_gpt_messages: 
        if final_response_text in message_item: 
            responsses_in_case_of_looping = [
                "Расскажи подробнее о том что ты чувствуешь, я попробую помочь", 
                f"{user_name}, ты со всем справишься! Как я могу тебе помочь?", 
                "Представляю что ты чувствуешь сейчас... Как я могу тебе помочь?", 
                "Я бы тебя обняла сейчас, если была человеком <3", 
                f"{user_name}, как я могу помочь тебе в этой ситуации?", 
                "Расскажешь подробнее об этом?"
            ]
            rand_item = random.randint(0, len(responsses_in_case_of_looping)-1)
            final_response_text = responsses_in_case_of_looping[rand_item]

    # checking if GPT respond with empty text
    if final_response_text == '' or final_response_text == ' ': 
        final_response_text = "Извини, я не поняла. Попробуешь переформулировать?"
    
    print(f'--> final response text: {final_response_text}')
    return final_response_text
