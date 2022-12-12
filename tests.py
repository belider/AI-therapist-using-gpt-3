from decorators import *
import psycopg2
from database_class import Database 
from bot import capitalize_sentences, informalize_russian_text

# db_test = Database()

# @print_postgre_exception
# def test_db_exceptions(db): 
#     print('щас будет ошибка')
#     query = f"""INVALID SQL REQUEST AHAHAHAAHHA"""
#     db.execute_select_query(query)

# testing decorator for postgress expeptions
# test_db_exceptions(db_test)

# testing gpt completion
prompt = "User: Tell me how to overscome depression\nTherapist:"
# print(create_gpt_response(prompt))

# response = openai.Completion.create(
#     model="text-davinci-002",
#     prompt=prompt,
#     max_tokens = 500,
#     n = 2,
#     temperature=0.5,
#     stop="User: "
#     )

response = {
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "logprobs": None,
      "text": "\n\nThere are a number of things that you can do to overcome depression. First, it is important to understand that depression is a real illness that can be treated. If you are feeling depressed, it is important to talk to your doctor or a mental health professional. They can help you figure out what is causing your depression and how to best treat it.\n\nThere are also a number of things that you can do on your own to help manage your depression. Some things that may help include:\n\n-Exercising regularly\n-Eating a healthy diet\n-Getting enough sleep\n-Spending time with friends and family\n-Doing things that you enjoy\n\nIf you are feeling depressed, it is important to reach out for help. There are people who can help you and there are things that you can do to make yourself feel better."
    },
    {
      "finish_reason": "stop",
      "index": 1,
      "logprobs": None,
      "text": "\n\nThere are many ways that people can overcome depression. Some people may need medication to help them get to a healthy state, while others may need therapy or other forms of treatment. It is important to work with a professional to figure out what will work best for you."
    }
  ],
  "created": 1669985320,
  "id": "cmpl-6Izl2mAcBBWGDHaV4NzSwV5IEqnWZ",
  "model": "text-davinci-002",
  "object": "text_completion",
  "usage": {
    "completion_tokens": 230,
    "prompt_tokens": 14,
    "total_tokens": 244
  }
}

# print(response["id"])
# print(response["model"])
# print(response["usage"]["total_tokens"])

# query = "select user_name from users where user_id=-1001868679303"
# res = db_test.execute_select_query(query)
# print(res)

# if res == []:
#     print('no name found')

# name_list = ['Маша', 'anton', 'Санек', 'Боба', 'Женя',
#              'Саша', 'Алекс Л', 'Иван', 'Марк', 'Поля', 'Никита']

# import pymorphy2
# morph = pymorphy2.MorphAnalyzer()
# # from translate import Translator
# # translator= Translator(from_lang="english", to_lang="russian")
# from googletrans import Translator
# translator = Translator()

# for name in name_list:
#     gender = morph.parse(name)[0].tag.gender
#     if gender == None or gender == 'neut': 
#        # translating a name
#        name = translator.translate(name, dest='ru').text
#        gender =  morph.parse(name)[0].tag.gender
#     print('{:<15} {}'.format(name, gender))
