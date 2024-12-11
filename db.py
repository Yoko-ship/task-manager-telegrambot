import psycopg2

connection = psycopg2.connect("postgresql://telegram_mdvg_user:OrWpseJ1qBK1Nmt3Fs5YRmcBd8nKhMSJ@dpg-ctconktds78s739i3o10-a/telegram_mdvg")
connection.autocommit = True

cursor = connection.cursor()