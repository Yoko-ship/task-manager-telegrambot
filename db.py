from config import host,password,dbname,user,port
import psycopg2 as psc
connection = psc.connect(
        host=host,
        user=user,
        password=password,
        database=dbname,
        port=port
)
connection.autocommit = True

cursor = connection.cursor()