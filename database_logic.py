
def insert_message_in_db(db, user_id, is_bot, message_text, message_timestamp): 
    insert_query = f""" INSERT INTO messages (user_id, msg_type, msg_text, msg_dt) 
                        VALUES ({user_id}, {is_bot}, '{message_text}', TIMESTAMP '{message_timestamp}') """
    db.execute_insert_query(insert_query)

def get_username_by_userid(db, user_id): 
    select_query = f"""select user_name from users where user_id = {user_id}"""
    user_name = db.execute_select_query(select_query)[0][0]
    return user_name

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

def set_or_update_username(db, user_id, user_name, user_tg_nick):
    query = f"""UPDATE users SET user_id={user_id}, user_name='{user_name}', tg_nick='{user_tg_nick}' WHERE user_id={user_id};
                INSERT INTO users (user_id, user_name, tg_nick)
                    SELECT {user_id}, '{user_name}', '{user_tg_nick}'
                    WHERE NOT EXISTS (SELECT 1 FROM users WHERE user_id={user_id});"""
    db.execute_insert_query(query)
    print(f"name {user_name} inserted in users DB")

def get_last_user_message(db, user_id): 
    select_query = f"""SELECT msg_text from messages where user_id={user_id} and msg_type = false order by msg_dt desc limit 1"""
    last_user_message = db.execute_select_query(select_query)[0]
    last_user_message = str(last_user_message[0])

    return last_user_message