import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="mydb1",
        user="postgres",
        password="aaryaan",
        host="localhost",
        port="5432"
    )