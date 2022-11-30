import psycopg2
import sys

def print_postgre_exception(func): 
    def wraped_func(db, *args, **kwargs): 
        try: 
            result = func(db, *args, **kwargs)
            return result
        except Exception as err:
            # get details about the exception
            err_type, err_obj, traceback = sys.exc_info()

            # get the line number when exception occured
            line_num = traceback.tb_lineno
            # print the connect() error
            print ("\npsycopg2 ERROR:", err, "on line number:", line_num)
            print ("psycopg2 traceback:", traceback, "-- type:", err_type)

            # psycopg2 extensions.Diagnostics object attribute
            print ("\nextensions.Diagnostics:", err.diag)

            # print the pgcode and pgerror exceptions
            # print ("pgerror:", err.pgerror)
            print ("pgcode:", err.pgcode, "\n")

            db.conn.rollback()
            return None
    return wraped_func
