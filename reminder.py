import telebot 
from db import cursor
from datetime import datetime
from pytz import timezone
import re
import os
import time
from dotenv import load_dotenv
from flask import Flask,request


app = Flask(__name__)
local_time = datetime.now(timezone("Asia/Tashkent")).strftime("%H:%M")
date = datetime.now().date()
sorted_data = datetime.strftime(date,"%d-%m-%Y")
load_dotenv()

user_table = """
        CREATE TABLE IF NOT EXISTS telegram_user(
                ID SERIAL PRIMARY KEY,
                user_id INT NOT NULL UNIQUE
        )
"""

create_table = """
        CREATE TABLE IF NOT EXISTS telegram(
        ID SERIAL PRIMARY KEY,
        Name VARCHAR NOT NULL,
        Date VARCHAR NOT NULL,
        Time VARCHAR NOT NULL,
        user_id INT NOT NULL,
        FOREIGN KEY(user_id)
        REFERENCES telegram_user(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
"""


cursor.execute(user_table)
cursor.execute(create_table)
api_token = os.getenv("API_KEY")
bot = telebot.TeleBot(api_token)


@app.route("/setup",methods=["GET","POST"])
def setup():
    webhook_url = "https://task-manager-telegrambot-1.onrender.com/webhook"
    success = bot.set_webhook(url=webhook_url)
    if success:
        return "Webhook успешно установлен",200
    else:
         return "Ошибка установки вебхука",500

@app.route("/webhook",methods=["POST"])
def webhook():
    try:
        json_str = request.get_data(as_text=True)
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "Ok",200
    except Exception as e:
         print(f"Произошла ошибка: {e} ")

@app.route("/",methods=["GET"])
def home():
    return "Сервер работает успешно"

def set_reminder(target_data,target_time,message,text):
        target_datatime = datetime.strptime(f"{target_data} {target_time}","%d.%m.%Y %H:%M")
        bot.send_message(message.from_user.id,"Напоминание успешно установлено")

        while datetime.now() < target_datatime:
                time.sleep(1)
        bot.send_message(message.from_user.id,f"Напоминаю про задачу:{text}")

@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, 
                     "Привет! Я бот-напоминалка. Доступные команды:\n"
                     "/help - Помощь\n"
                     "/info - Информация о боте\n"
                     "/reminder - Установить напоминание\n"
                     "/create - Создать новую задачу\n"
                     "/my_task - Посмотреть список задач\n"
                     "/delete_task - Удалить задачу\n"
                     "/edit_task - Редактировать задачу")
    

@bot.message_handler(commands=["help"])
def help_message(message):
    bot.send_message(message.chat.id, 
                     "Помощь по боту:\n"
                     "- /reminder: Установить напоминание о задаче\n"
                     "- /create: Создать новую задачу\n"
                     "- /my_task: Показать все задачи\n"
                     "- /delete_task: Удалить задачу по её ID\n"
                     "- /edit_task: Изменить текст существующей задачи\n\n"
                     "Введите команду, чтобы узнать больше.")

@bot.message_handler(commands=["info"])
def informations(message):
    bot.send_message(message.chat.id, 
                     "Этот бот позволяет вам создавать задачи и получать напоминания о них. "
                     "Вы можете управлять своими задачами через команды. Для начала используйте /help.")

@bot.message_handler(commands=['my_task'])
def my_task(message):
    user_id = message.from_user.id
    query = "SELECT * FROM telegram WHERE user_id = %s"
    cursor.execute(query,[user_id])
    all_informations = cursor.fetchall()
    if all_informations:
        for i in all_informations:
            text = (f"ID: {i[0]}\n"
                    f"Задача: {i[1]}\n"
                    f"Дата: {i[2]}\n"
                    f"Время: {i[3]}")
            bot.send_message(message.from_user.id, text)
    else:
        bot.send_message(message.chat.id, "У вас пока нет задач. Создайте новую с помощью команды /create.")

@bot.message_handler(content_types=["text"])
def text_handler(message):
    if message.text == "Привет":
        start_message(message)

    elif message.text == "/reminder":
        bot.send_message(message.from_user.id, 
                         "Введите дату, время и ID задачи в формате:\n"
                         "день.месяц.год / час:минута, ID\n"
                         "Например: 12.12.2024 / 14:30, 1")
        bot.register_next_step_handler(message, reminder_handler)

    elif message.text == "/create":
        bot.send_message(message.from_user.id, "Введите текст задачи:")
        bot.register_next_step_handler(message, create_task)

    elif message.text == "/delete_task":
        bot.send_message(message.from_user.id, 
                         "Введите ID задачи, которую вы хотите удалить.\n"
                         "Чтобы узнать ID задачи, используйте команду /my_task.")
        bot.register_next_step_handler(message, delete_task)

    elif message.text == "/edit_task":
        bot.send_message(message.from_user.id, 
                         "Введите ID задачи и новый текст через запятую:\n"
                         "ID, Новый текст задачи")
        bot.register_next_step_handler(message, edit_task)

    else:
        bot.send_message(message.chat.id, 
                         "Я не понимаю ваш запрос. Пожалуйста, используйте одну из доступных команд: /help, /info, /reminder.")

def reminder_handler(message):
    task = message.text
    user_id = message.from_user.id
    time = re.split(r'[/,]', task)
    query = "UPDATE telegram SET Date = %s, Time = %s WHERE id = %s AND user_id = %s"
    try:
        cursor.execute(query, [time[0], time[1], time[2],user_id])
        task_text = "SELECT Name FROM telegram WHERE id = %s AND user_id=%s"
        cursor.execute(task_text, [time[2],user_id])
        information = cursor.fetchone()
        if information :
            set_reminder(time[0], time[1], message, str(information))
        else:
            bot.send_message(message.from_user.id, 
                             f"Задача с ID {time[2]} не найдена. "
                             "Используйте /my_task, чтобы посмотреть список задач.")
    except IndexError:
        bot.send_message(message.from_user.id, 
                         "Вы не указали ID задачи. Убедитесь, что формат данных корректен.")
    except ValueError:
        bot.send_message(message.from_user.id, 
                         "Пожалуйста, укажите дату и время в формате: 'день.месяц.год / час:минута'.")
    except Exception:
        bot.send_message(message.from_user.id, "Произошла ошибка. Попробуйте ещё раз.")

def create_task(message):
    task = message.text
    user_id = message.from_user.id
    query_check = "SELECT user_id FROM telegram_user WHERE user_id = %s"
    cursor.execute(query_check,[user_id])
    info = cursor.fetchone()
    if info:
        query = "INSERT INTO telegram(Name, Date, Time,user_id) VALUES(%s, %s, %s,%s)"
        cursor.execute(query, [task, sorted_data, local_time,user_id])
        bot.send_message(message.from_user.id, "Задача успешно добавлена!")
                  
    else:
        user_query = "INSERT INTO telegram_user(user_id) VALUES(%s)"
        cursor.execute(user_query,[user_id])
        query = "INSERT INTO telegram(Name, Date, Time,user_id) VALUES(%s, %s, %s,%s)"
        cursor.execute(query, [task, sorted_data, local_time,user_id])
        bot.send_message(message.from_user.id, "Задача успешно добавлена!")

def delete_task(message):
    task = message.text
    user_id = message.from_user.id
    if task == "/my_task":
        my_task(message)
    else:

        try:
                query_check = "SELECT Name FROM telegram WHERE id = %s AND user_id = %s"
                cursor.execute(query_check,[task,user_id])
                info = cursor.fetchone()
                if info:
                     
                        query = "DELETE FROM telegram WHERE id = %s AND user_id = %s"
                        cursor.execute(query, [task,user_id]) 
                        bot.send_message(message.from_user.id, "Задача успешно удалена!")
                else:
                     bot.send_message(message.from_user.id,"Задачи с текущим id не существует")
        except Exception:
                bot.send_message(message.from_user.id, "Пожалуйста, введите корректный ID задачи.")

def edit_task(message):
    task = message.text
    user_id = message.from_user.id
    try:
        task_id, new_task = task.split(",")
        query_check = "SELECT Name FROM telegram WHERE ID = %s AND user_id = %s"
        cursor.execute(query_check,[task_id,user_id])
        info = cursor.fetchone()
        if info:
             
                query = "UPDATE telegram SET Name = %s WHERE ID = %s AND user_id = %s"
                cursor.execute(query, [new_task.strip(), task_id.strip(),user_id])
                bot.send_message(message.from_user.id, 
                                "Текст задачи успешно обновлён! Используйте /my_task, чтобы посмотреть изменения.")
        else:
             bot.send_message(message.from_user.id,"Задача с текущим Id не существует")
    except Exception:
        bot.send_message(message.from_user.id, "Ошибка при редактировании задачи. Проверьте формат ввода.")




if __name__ == "__main__":
    port = 5000
    print(f"Сервер работает на порте{port}")
    app.run(host='0.0.0.0',port=port)
