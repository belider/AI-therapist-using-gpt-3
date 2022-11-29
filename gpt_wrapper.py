import openai

def create_gpt_response(prompt):
    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=prompt,
        max_tokens = 500,
        n = 2,
        temperature=0.5,
        stop="Я: "
        )
    
    return response

def messages_history_to_text_dialogue(messages, max_dialogue_len=3000): 
    dialogue = ''
    
    for msg in reversed(messages):
        if msg[3] in ['/start', '/newsession']: 
            # this is command message
            continue
        if len(dialogue) > max_dialogue_len: 
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

def get_not_repeating_not_empty_response(response_candidates, messages_history):
    # getting gpt responses from dialogue
    last_gpt_messages = []
    for el in messages_history: 
        if el[2] == True:
            last_gpt_messages.append(el[3].strip().lower())
    
    print(f'----> last gpt messages: {last_gpt_messages}\n')
    
    responses = []
    responses.append(response_candidates.choices[0].text.lower().strip())
    responses.append(response_candidates.choices[1].text.lower().strip())
    print(f'-----> response[0]: {responses[0]}')
    print(f'-----> response[1]: {responses[0]}\n')

    if not responses[0] in last_gpt_messages: 
        final_response_text = response_candidates.choices[0].text
        i = 0
    else:  
        final_response_text = response_candidates.choices[1].text
        i = 1

    print(f'--> final response - {i}')

    if final_response_text == '' or final_response_text == ' ': 
        final_response_text = "Извини, я не поняла. Попробуешь переформулировать?"
    
    return final_response_text
