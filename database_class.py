import os
import psycopg2

class Database: 
    conn = None
    cursor = None

    def __init__(self):
        print('connecting to database...')

        db_name = os.getenv('PGDATABASE')
        db_user = os.getenv('PGUSER')
        db_pass = os.getenv('PGPASSWORD')
        db_host = os.getenv('PGHOST')
        db_port = os.getenv('PGPORT')

        self.conn = psycopg2.connect(database=db_name, user=db_user, password=db_pass, host=db_host, port=db_port)
        
        self.cursor = self.conn.cursor()

        self.cursor.execute("select version()")
        # read a single row from query result using fetchone() method.
        data = self.cursor.fetchone()
        print("Connection established to: ", data)
    
    def __del__(self):        
        if (self.conn is not None and self.cursor is not None): 
            print('closing database connection...')
            self.cursor.close()
            self.conn.close()
    
    def execute_insert_query(self, query): 
        self.cursor.execute(query)
        self.conn.commit()

    def execute_select_query(self, query): 
        self.cursor.execute(query)
        return self.cursor.fetchall()