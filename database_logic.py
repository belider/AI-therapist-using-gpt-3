from decorators import *

@print_postgre_exception
def insert_message_in_db(db, user_id, is_bot, message_text, message_timestamp): 
    message_text = str(message_text).replace("'", "''")
    print(f"message_text: {message_text}")
    insert_query = f""" INSERT INTO messages (user_id, msg_type, msg_text, msg_dt) 
                        VALUES ({user_id}, {is_bot}, '{message_text}', TIMESTAMP '{message_timestamp}') """
    db.execute_insert_query(insert_query)

@print_postgre_exception
def get_username_and_gender_by_userid(db, user_id): 
    select_query = f"""select user_name, gender from users where user_id = {user_id}"""
    res = db.execute_select_query(select_query)
    if res == []:
        user_name = 'Аноним'
        gender = 'masc'
    else:
        user_name = res[0][0]
        gender = res[0][1]
    return (user_name, gender)

@print_postgre_exception
def get_messages_from_last_user_command(db, user_id):
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
    messages_from_last_command = db.execute_select_query(select_query)
    return messages_from_last_command

@print_postgre_exception
def set_or_update_username(db, user_id, user_name, user_tg_nick, user_tg_name, gender):
    query = f"""UPDATE users SET user_id={user_id}, user_name='{user_name}', tg_nick='{user_tg_nick}', tg_name='{user_tg_name}', gender='{gender}' WHERE user_id={user_id};
                INSERT INTO users (user_id, user_name, tg_nick, tg_name, gender)
                    SELECT {user_id}, '{user_name}', '{user_tg_nick}', '{user_tg_name}', '{gender}'
                    WHERE NOT EXISTS (SELECT 1 FROM users WHERE user_id={user_id});"""
    db.execute_insert_query(query)
    print(f"name {user_name} inserted in users DB")

@print_postgre_exception
def get_last_user_message(db, user_id): 
    select_query = f"""SELECT msg_text from messages where user_id={user_id} and msg_type = false order by msg_dt desc limit 1"""
    last_user_message = db.execute_select_query(select_query)[0]
    last_user_message = str(last_user_message[0])

    return last_user_message

@print_postgre_exception
def insert_gpt_request_to_db(db, request_id, user_id, request_dt, prompt_text, completion_text, total_tokens, model, cost):
    prompt_text = prompt_text.replace("'", "''")
    completion_text = completion_text.replace("'", "''")
    insert_query = f""" INSERT INTO gpt_requests (request_id, user_id, request_dt, prompt_text, completion_text, total_tokens, model, cost) 
                        VALUES ('{request_id}', {user_id}, TIMESTAMP '{request_dt}', '{prompt_text}', '{completion_text}', {total_tokens}, '{model}',{cost}) """
    db.execute_insert_query(insert_query)

@print_postgre_exception
def get_paid_limit_and_status_by_user(db, user_id): 
    select_query = f"""select sum(paid_messages)
                        from user_paid_limits
                        where user_id={user_id}"""
    messages_limit = db.execute_select_query(select_query)[0][0]
    
    messages_sent = 0
    select_query = f"""select count(distinct request_id) 
                        from gpt_requests
                        where user_id={user_id}"""
    messages_sent = db.execute_select_query(select_query)[0][0]
    print(f'messages sent = {messages_sent}')
    print(f'paid messages limit = {messages_limit}')
    
    paid_limit_status = ''
    if messages_sent > messages_limit and messages_limit==50: 
        paid_limit_status = 'trial ended'
    elif messages_sent > messages_limit and messages_limit > 100:
        paid_limit_status = 'paid plan ended'
    elif messages_sent < messages_limit:
        paid_limit_status = 'paid'
    
    return (messages_limit, paid_limit_status)

@print_postgre_exception
def insert_analytics_event_to_db(db, user_id, event_name, event_params={}):
    event_params = str(event_params).replace("'", '"')
    query = f"""INSERT INTO events (user_id, event_name, event_parameters, event_dt) 
                VALUES (
                    {user_id}, 
                    '{event_name}', 
                    '{event_params}', 
                    now()
                ) """
    db.execute_insert_query(query)