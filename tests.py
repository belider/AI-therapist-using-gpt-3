from decorators import *
import psycopg2
from database_class import Database 
from gpt_wrapper import *

# db_test = Database()

@print_postgre_exception
def test_db_exceptions(db): 
    print('щас будет ошибка')
    query = f"""INVALID SQL REQUEST AHAHAHAAHHA"""
    db.execute_select_query(query)

# testing decorator for postgress expeptions
# test_db_exceptions(db_test)

# testing gpt completion
print(create_gpt_response("Я: Расскажи как правильно питаться по пунктам.\nТерапевт:"))