# Возьми только сообщения юзера где не команда
# Посчитай для каждого last messagess и last command

# построй dialogue history
# построй prompt на основе dialogue history и last command

# как бы ты это делал в случае если пришло реальное сообщение
# (просто скопируй логику)

# Для каждого prompt + response_message посчитай кол-во токенов
# с помощью апишки (?) которая считает токены или 1символ=1токен

# заинзерть результат для этого message в gpt_requests

from gpt_wrapper import *
from database_logic import *
from database_class import Database
from transformers import GPT2Tokenizer

db = Database()

start_msg_id = 970
query = f"select * from messages where msg_text not like '/%' and msg_type = false and msg_id >= {start_msg_id}"
user_messages = db.execute_select_query(query)


def get_response_by_message(msg_id, user_id):
    query = f"""select gpt_response
from (
    select msg_id, 
        msg_text, 
        msg_type, 
        lead(msg_text) over (partition by user_id order by msg_dt) as gpt_response
    from messages
    where user_id = '{user_id}'
) as msgs 
where msgs.msg_id = {msg_id}"""
    gpt_response = db.execute_select_query(query)[0][0]
    return gpt_response

# testing
# get_response_by_message(msg_id=716, user_id=27147366)

def get_messages_from_last_command_by_msg_id(db, user_id, msg_id):
    select_query = f"""select *
                        from messages m
                        join (select user_id, 
                                        max(msg_id) last_command 
                                from messages 
                                where msg_text like '/%' 
                                    and msg_id <= {msg_id}
                                group by user_id
                        ) lm on lm.user_id = m.user_id 
                            and m.msg_id >= lm.last_command 
                            and m.msg_id <= {msg_id}
                        where m.user_id = {user_id}
                        order by msg_id
                        """
    messages_from_last_command = db.execute_select_query(select_query)
    return messages_from_last_command

# testing
# print(get_messages_from_last_command_by_msg_id(db, user_id=288939647, msg_id=77))

def count_tokens(input: str):
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    res = tokenizer(input)['input_ids']
    return len(res)

# testing
# print(count_tokens("Здравствуйте, меня зовут Терапевт. Как ваши дела?"))

for row in user_messages:
    msg_text = row[3]
    user_id = row[1]
    msg_dt = row[4]
    msg_id = row[0]

    print(f'--> user says "{msg_text}", msg_id={msg_id}, user_id={user_id}')

    # select all messages from the previous command
    messages_from_last_command = get_messages_from_last_command_by_msg_id(db, user_id, msg_id)

    # getting user name
    user_name = get_username_and_gender_by_userid(db, user_id)
    
    prompt = construct_prompt_from_messages_history(messages_from_last_command, user_name)
    gpt_response = get_response_by_message(msg_id, user_id)
    if prompt == None or gpt_response == None:
        #probably smth wrong
        continue
    else: 
        total_tokens = count_tokens(prompt + gpt_response)
        cost = total_tokens * 0.02 / 1000

        print('--------------')
        print('--> response:')
        print(gpt_response)
        print('--------------')
        print(f'--> total tokens={total_tokens}, cost={cost}')
        print('--------------')

        insert_gpt_request_to_db(db, request_id='cmpl-'+str(msg_id), user_id=user_id, request_dt=msg_dt, prompt_text=prompt, completion_text=gpt_response, total_tokens=total_tokens, model='text-davinci-002', cost=cost)
        print(f'>>>>> msg_id {msg_id} inserted to gpt_requests <<<<<<')
    # break
