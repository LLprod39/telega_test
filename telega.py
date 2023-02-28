# проект для телеграм бота
import telebot
from telebot import types
import random
import datetime
import os
import sqlite3
import time
import re
import threading

# токент бота и создание бота
bot = telebot.TeleBot('1911225697:AAG0PEEb4xTee0vgTWGlxW-UkbIQ0MD9fU0')


# подключаемся к базе данных
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()


# создаем таблицу, если ее нет В НЕЙ будет храниться сообщение будет отпровлять бот
cursor.execute("""CREATE TABLE IF NOT EXISTS message (
    message_ID TEXT,
    message_start TEXT,
    message_otmena TEXT,
    message_zapis TEXT,
    message_predoplata TEXT,
    message_admin TEXT,
    message_admin_otmena TEXT,
    message_admin_ok TEXT
)""")


# создаем таблицу, если ее нет В НЕЙ ХРАНИТСЯ ID администратор бота и его имя
cursor.execute("""CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER,
    admin_name TEXT
)""")


# создаем таблицу, если ее нет В НЕ ХРОНЯТСЯ ИМЯ СЕРВИСА И ЕГО ЦЕНА
cursor.execute("""CREATE TABLE IF NOT EXISTS nameprice (
    servis TEXT,
    price TEXT
)""")


# создаем таблицу, если ее нет В НЕЙ ХРАНИТСЯ ВРЕМЯ СВОБОДНЫХ МЕСТ СЕРВИСА
cursor.execute("""CREATE TABLE IF NOT EXISTS free_oryn (
    user_id INTEGER,
    time_servis TEXT,
    data_servis TEXT
)""")


# создаем таблицу, если ее нет В НЕЙ ХРАНИТСЯ ДАННЫЕ О ПОЛЬЗОВАТЕЛЕ
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    first_name TEXT,
    last_name TEXT,
    username TEXT
)""")


# создаем таблицу, если ее нет В НЕЙ ХРАНИТСЯ ДАННЫЕ О ПОЛЬЗОВАТЕЛЕ КОТОРЫЙ ВНЕСЛИ ПРЕДОПЛАТУ И ЗАПИСАЛИСЬ НА СЕРВИС
cursor.execute("""CREATE TABLE IF NOT EXISTS predoplata (
    user_id INTEGER,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    phone TEXT,
    time_servis TEXT,
    data_servis TEXT,
    name_servis TEXT,
    price_servis TEXT
)""")



# обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # проверяем есть ли в таблице пользователь с таким id если нет то добавляем его в таблицу users и выводим приветствие с его именем и фамилией
    cursor.execute(f"SELECT user_id FROM users WHERE user_id = {message.from_user.id}")
    if cursor.fetchone() is None:
        cursor.execute(f"INSERT INTO users VALUES ({message.from_user.id}, '{message.from_user.first_name}', '{message.from_user.last_name}', '{message.from_user.username}')")
        conn.commit()
        # отпровляем приветсвие взяв текст из базы данных message из ячейки message_start и отправляем его пользователю и его имя и фамилию
        cursor.execute(f"SELECT message_start FROM message")
        message_start = cursor.fetchone()
        bot.send_message(message.chat.id, f'{message_start[0]} {message.from_user.first_name} {message.from_user.last_name}!')

    else:
        cursor.execute(f"SELECT message_start FROM message")
        message_start = cursor.fetchone()
        bot.send_message(message.chat.id,
                         f'{message_start[0]} {message.from_user.first_name} {message.from_user.last_name}!')


    # создаем клавиатуру с кнопкой свободные места
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Свободные места')
    cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        keyboard.row('/admin')
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard)



# обработчик кнопки "Свободные места"
@bot.message_handler(func=lambda message: message.text == 'Свободные места')
def free_oryn(message):
    cursor.execute(f"SELECT user_id FROM predoplata WHERE user_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row('Посмотреть запись')
        keyboard.row('Отменить запись')
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cursor.execute(f"SELECT time_servis, data_servis FROM free_oryn")
        times_and_dates = cursor.fetchall()
        for i in range(len(times_and_dates)):
            keyboard.row(f'{times_and_dates[i][0]} {times_and_dates[i][1]}')
        # добовляем кнопку назад и если пользователь админ то добовляем кнопку админ панель
        keyboard.row('Назад')
        cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        keyboard.row('/admin')


    bot.send_message(message.chat.id, 'Выберите время и дату', reply_markup=keyboard)
# если свободных мест нет то выводим сообщение о том что свободных мест нет
    if len(times_and_dates) == 0:
        bot.send_message(message.chat.id, 'Свободных мест нет')
        cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
        if cursor.fetchone() is not None:
            keyboard.row('/admin')
        bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard)

# обработчик выбранного времени и даты
@bot.message_handler(func=lambda message: message.text.endswith('23'))
def nameprice(message):
    # проверяем есть ли в таблице predoplata данные о пользователе если нет  выписываем в ячейку time_servis и data_servis время и дату которое выбрал пользователь если есть то отпровлям сообщение о том что он уже записан на этот сервис
    cursor.execute(f"SELECT user_id FROM predoplata WHERE user_id = {message.from_user.id}")
    if cursor.fetchone() is None:
        # проверяем, что выбранное пользователем время и дата есть в таблице free_oryn
        cursor.execute(
            f"SELECT * FROM free_oryn WHERE time_servis = '{message.text[:5]}' AND data_servis = '{message.text[6:]}'")
        if cursor.fetchone() is None:
            bot.send_message(message.chat.id, 'Выбранное время и дата уже заняты, выберите другое')
            return

        # сохраняем выбранное пользователем время и дату в атрибуте message.chat
        message.chat.time_servis = message.text[:5]
        message.chat.data_servis = message.text[6:]

        # записываем в таблицу predoplata данные о пользователе и выписываем в ячейку time_servis и data_servis время и дату которое выбрал пользователь
        cursor.execute(
            f"SELECT user_id, first_name, last_name, username FROM users WHERE user_id = {message.from_user.id}")
        user = cursor.fetchone()
        cursor.execute(
            f"INSERT INTO predoplata VALUES ({user[0]}, '{user[1]}', '{user[2]}', '{user[3]}', '', '{message.text[:5]}', '{message.text[6:]}', '', '')")
        conn.commit()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cursor.execute(f"SELECT servis, price FROM nameprice")
        services_and_prices = cursor.fetchall()
        for i in range(len(services_and_prices)):
            keyboard.row(f'{services_and_prices[i][0]} {services_and_prices[i][1]}')
        bot.send_message(message.chat.id, 'Выберите услугу', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Вы уже записаны на этот сервис')

    # после выбора услуги спрашиваем номер телефона и проверяем его на правильность написание
    @bot.message_handler(func=lambda message: message.text.endswith('тнг'))
    def phone(message):
        # записываем в таблицу predoplata данные тому пользователю который выбрал услугу и выписываем в ячейку name_servis и price_servis название услуги и ее цену
        cursor.execute(
            f"SELECT user_id, first_name, last_name, username FROM users WHERE user_id = {message.from_user.id}")
        user = cursor.fetchone()
        cursor.execute(
            f"UPDATE predoplata SET name_servis = '{message.text[:-4]}', price_servis = '{message.text[-4:]}' WHERE user_id = {user[0]}")
        conn.commit()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row('Назад')
        bot.send_message(message.chat.id, 'Введите номер телефона', reply_markup=keyboard)







        @bot.message_handler(func=lambda message: message.text.startswith('87'))
        def predoplata(message):
            if len(message.text) >= 7 and message.text.startswith('87') and all(c.isdigit() for c in message.text[2:]):
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.row('Свободные места')
                cursor.execute(f"SELECT message_predoplata FROM message")
                message_predoplata = cursor.fetchone()
                bot.send_message(message.chat.id, message_predoplata[0], reply_markup=keyboard)



                # записываем в таблицу predoplata данные тому пользователю который выбрал услугу и выписываем в ячейку phone номер телефона
                cursor.execute(
                    f"SELECT user_id, first_name, last_name, username FROM users WHERE user_id = {message.from_user.id}")
                user = cursor.fetchone()
                cursor.execute(f"UPDATE predoplata SET phone = '{message.text}' WHERE user_id = {user[0]}")
                conn.commit()

                # смотрим в базе данных predoplata этого пользоватял и если данные которые есть совподают с данныеми из таблицы free_oryn то удаляем эти данные из таблицы free_oryn
                cursor.execute(
                    f"SELECT user_id, first_name, last_name, username, phone, time_servis, data_servis, name_servis, price_servis FROM predoplata WHERE user_id = {user[0]}")
                user = cursor.fetchone()
                cursor.execute(
                    f"DELETE FROM free_oryn WHERE time_servis = '{user[5]}' AND data_servis = '{user[6]}'")
                conn.commit()



                # смотрим в базе данных predoplata этого пользоватял и если все данные заполнены то отправляем сообщение в телеграмм админу о том что кто то записался и выводим все данные о пользователе и услуге которую он выбрал
                cursor.execute(
                    f"SELECT user_id, first_name, last_name, username, phone, time_servis, data_servis, name_servis, price_servis FROM predoplata WHERE user_id = {user[0]}")
                user = cursor.fetchone()
                if user[4] != '' and user[5] != '' and user[6] != '' and user[7] != '' and user[8] != '':
                    bot.send_message(1041149302,
                                     f'Пользователь: {user[1]} {user[2]} @{user[3]}\nНомер телефона: {user[4]}\nВремя записи: {user[5]} {user[6]}\nУслуга: {user[7]}\nЦена: {user[8]}')



                    # отпровляем админу еще одно сообще с двумя кнопками Подтвердить и Отменить
                    keyboard = types.InlineKeyboardMarkup()
                    key_yes = types.InlineKeyboardButton(text='Подтвердить', callback_data='yes')
                    keyboard.add(key_yes)
                    key_no = types.InlineKeyboardButton(text='Отменить', callback_data='no')
                    keyboard.add(key_no)
                    bot.send_message(1041149302, 'Подтвердить или отменить запись?', reply_markup=keyboard)

                    # если нажата кнопка подвердить запись то оставляем все как есть
                    # если нажата кнопка подвердить запись то оставляем все как есть
                    @bot.callback_query_handler(func=lambda call: True)
                    def callback_worker(call):
                        if call.data == 'yes':
                            bot.send_message(1041149302, 'Запись подтверждена')
                            # отпровляем пользователю чью запись отменили сообщение о том что его запись отменена, сообщение берем из базы данных messages из ячейки message_otmena
                            cursor.execute(f"SELECT message_admin_ok FROM message")
                            message = cursor.fetchone()
                            bot.send_message(call.from_user.id, message[0])

                        elif call.data == 'no':
                            # если нажата кнопка отменить запись то удаляем все данные о пользователе, который записался, из таблицы predoplata  и возвращаем данные в таблицу free_oryn, и отправляем сообщение в телеграмм админу о том, что запись отменена
                            cursor.execute( f"SELECT user_id, first_name, last_name, username, phone, time_servis, data_servis, name_servis, price_servis FROM predoplata WHERE user_id = {call.from_user.id}")
                            user = cursor.fetchone()
                            cursor.execute(f"DELETE FROM predoplata WHERE user_id = {user[0]}")
                            conn.commit()
                            cursor.execute(f"INSERT INTO free_oryn (time_servis, data_servis) VALUES ('{user[5]}', '{user[6]}')")
                            conn.commit()
                            bot.send_message(1041149302, 'Запись отменена')
                            # отпровляем пользователю чью запись отменили сообщение о том что его запись отменена, сообщение берем из базы данных messages из ячейки message_otmena
                            cursor.execute(f"SELECT message_admin_otmena FROM message")
                            message = cursor.fetchone()
                            bot.send_message(call.from_user.id, message[0])






            else:
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.row('Назад')
                bot.send_message(message.chat.id, 'Введите номер телефона в таком формате 87******', reply_markup=keyboard)






# если пользователь нажал на кнопку Посмотреть запись то выводим ему информацию о его записи если она есть и если нет то выводим ему сообщение что у него нет записи на этот сервис
@bot.message_handler(func=lambda message: message.text == 'Посмотреть запись')
def check_record(message):
    cursor.execute(f"SELECT user_id, first_name, last_name, username, phone, time_servis, data_servis, name_servis, price_servis FROM predoplata WHERE user_id = {message.from_user.id}")
    user = cursor.fetchone()
    if user is not None:
        bot.send_message(message.chat.id, f'Ваша запись на сервис {user[7]} {user[5]} {user[6]}')
    else:
        bot.send_message(message.chat.id, 'У вас нет записи на этот сервис')

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Свободные места')





# если пользователь нажал на кнопку Отменить запись то удаляем его запись из таблицы predoplata и выводим ему сообщение что запись отменена и возвращаем его в меню, и возврощаем его запись в таблицу free_oryn чтобы другие пользователи могли записаться на это время
@bot.message_handler(func=lambda message: message.text == 'Отменить запись')
def cancel_record(message):
    cursor.execute(f"SELECT user_id, first_name, last_name, username, phone, time_servis, data_servis, name_servis, price_servis FROM predoplata WHERE user_id = {message.from_user.id}")
    user = cursor.fetchone()
    if user is not None:
        cursor.execute(f"DELETE FROM predoplata WHERE user_id = {message.from_user.id}")
        conn.commit()
        cursor.execute(f"INSERT INTO free_oryn (time_servis, data_servis) VALUES ('{user[5]}', '{user[6]}')")
        conn.commit()
        bot.send_message(message.chat.id, 'Запись отменена')
    else:
        bot.send_message(message.chat.id, 'У вас нет записи на этот сервис')

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Свободные места')
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard)





# обработчик кнопки "Назад" на шаге выбора услуги
@bot.message_handler(func=lambda message: message.text == 'Назад')
def cancel_service_selection(message):
    cursor.execute(f"SELECT user_id FROM predoplata WHERE user_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        cursor.execute(f"DELETE FROM predoplata WHERE user_id = {message.from_user.id}")
        conn.commit()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Свободные места')
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard)




# обработчик кнопки "Назад" на шаге ввода номера телефона
@bot.message_handler(func=lambda message: message.text == 'Назад' and hasattr(message.chat, 'phone'))
def cancel_phone_input(message):
    cursor.execute(f"SELECT user_id FROM predoplata WHERE user_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        cursor.execute(f"DELETE FROM predoplata WHERE user_id = {message.from_user.id}")
        conn.commit()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад')
    bot.send_message(message.chat.id, 'Выберите услугу', reply_markup=keyboard)




"""
# обработчик кнопки "Назад" на шаге выбора услуги
@bot.message_handler(func=lambda message: message.text == 'Назад')
def cancel_service_selection(message):
    cursor.execute(f"SELECT phone_number FROM predoplata WHERE user_id = {message.from_user.id}")
    result = cursor.fetchone()
    if result is not None and result[0] is not None:
        # пользователь уже заполнил номер телефона, не удаляем данные из базы данных
        pass
    else:
        cursor.execute(f"DELETE FROM predoplata WHERE user_id = {message.from_user.id}")
        conn.commit()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Свободные места')
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard) 
"""















#### тут идет код описаный для админ фкнций ####













# проверяем есть ли пользователь в базе admin если есть то даем ему доступ к админ панели
@bot.message_handler(commands=['admin'])
def admin(message):
    cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row('Свободные места')
        keyboard.row('Записанные')
        keyboard.row('Добавить Свободные места')
        keyboard.row('Удалить Свободные места')

        # доп функции
        keyboard.row('поменять имя Услуги')
        keyboard.row('Изменить цену сервиса')
        keyboard.row('Добавить Сервис')
        keyboard.row('Удалить Сервис')
        keyboard.row('Добавить Админа')
        keyboard.row('Удалить Админа')
        keyboard.row('Неподвержденные записи')
        keyboard.row('поменять приветствие Боту /start')
        keyboard.row('поменять сообщение, Дожидайтесь подтверждения записи')

        # доп функции

        bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к админ панели')

@bot.message_handler(func=lambda message: message.text == 'Записанные')
def zapisi(message):
    cursor.execute(f"SELECT user_id, first_name, last_name, username, phone, time_servis, data_servis, name_servis, price_servis FROM predoplata")
    users = cursor.fetchall()
    if not users:
        bot.send_message(message.chat.id, 'Записи не найдены')
        return

    keyboard = types.InlineKeyboardMarkup()
    for user in users:
        key_no = types.InlineKeyboardButton(text=f'Отменить {user[1]}', callback_data=f"delete:{user[1]}")
        keyboard.add(key_no)
        bot.send_message(message.chat.id, f'Пользователь: {user[1]} {user[2]} @{user[3]}\nНомер телефона: {user[4]}\nВремя записи: {user[5]} {user[6]}\nУслуга: {user[7]}\nЦена: {user[8]}', reply_markup=keyboard)


    # функция обработки нажатия на кнопку отменить запись по имени пользователя в базе данных и добовление в базу данных free_oryn дату на которую была запись и время
    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete:'))
    def delete(call):
        cursor.execute(f"SELECT user_id, first_name, last_name, username, phone, time_servis, data_servis, name_servis, price_servis FROM predoplata")
        users = cursor.fetchall()
        for user in users:
            if user[1] == call.data.split(':')[1]:
                cursor.execute(f"DELETE FROM predoplata WHERE user_id = {user[0]}")
                conn.commit()
                cursor.execute(f"INSERT INTO free_oryn (time_servis, data_servis) VALUES ('{user[5]}', '{user[6]}')")
                conn.commit()
                bot.send_message(call.message.chat.id, f'Запись отменена')
                # отпровляем пользователю сообщение что его запись отменена
                bot.send_message(user[0], f'Запись отменена')
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)












# если нажата кнопка добавить свободные места то запрашиваем время и дату в таком формате 12:00 01.01.2021 и добовляем в базу данных free_oryn данные которые ввел админ в таком формате time_servis 12:00 data_servis 01.01.2021
@bot.message_handler(func=lambda message: message.text == 'Добавить Свободные места')
def add_free_oryn(message):
    # мы должны проверять что сообщение пришло от админа и проверяем что в базе данных нет такого времени и даты и проверяем что введенное время и дата не пустое и соответствует формату
    cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row('Назад')
        bot.send_message(message.chat.id, 'Введите время и дату в таком формате 12:00 01.01.2021', reply_markup=keyboard)
        bot.register_next_step_handler(message, add_free_oryn2)
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к админ панели')


# обработчик ввода времени и даты
def add_free_oryn2(message):
    # проверяем что введенное время и дата не пустое и соответствует формату
    if message.text != 'Назад' and re.search(r'^\d{2}:\d{2} \d{2}\.\d{2}\.\d{4}$', message.text):
        time_servis, data_servis = message.text.split(' ')
        cursor.execute(f"SELECT time_servis, data_servis FROM free_oryn WHERE time_servis = '{time_servis}' AND data_servis = '{data_servis}'")
        if cursor.fetchone() is None:
            cursor.execute(f"INSERT INTO free_oryn (time_servis, data_servis) VALUES ('{time_servis}', '{data_servis}')")
            conn.commit()
            bot.send_message(message.chat.id, 'Свободное место добавлено')
        else:
            bot.send_message(message.chat.id, 'Такое время и дата уже существует')
    else:
        bot.send_message(message.chat.id, 'Неверный формат времени и даты')

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('/admin')
    keyboard.row('Добавить Свободные места')
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard)


######### функция кнопки  удаление свободного места

# если нажата кнопка удалить свободные места то выводим кнопки со свободоными местами и если кнопка нажата то удаляем выброное место из базы данных free_oryn
@bot.message_handler(func=lambda message: message.text == 'Удалить Свободные места')
def del_free_oryn(message):
    cursor.execute(f"SELECT time_servis, data_servis FROM free_oryn")
    free_oryn = cursor.fetchall()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for free in free_oryn:
        keyboard.row(f'{free[0]} {free[1]}')
    keyboard.row('Назад')
    bot.send_message(message.chat.id, 'Выберите свободное место', reply_markup=keyboard)
    bot.register_next_step_handler(message, del_free_oryn2)
    # после удаления свободного места возвращаемся в админ панель
    bot.register_next_step_handler(message, admin)
    # если свободных мест нет то выводим сообщение что свободных мест нет
    if len(free_oryn) == 0:
        bot.send_message(message.chat.id, 'Свободных мест нет')
        admin(message)

# удаление свободного места
def del_free_oryn2(message):
    time_servis = message.text.split()[0]
    data_servis = message.text.split()[1]
    cursor.execute(f"DELETE FROM free_oryn WHERE time_servis = '{time_servis}' AND data_servis = '{data_servis}'")
    conn.commit()
    bot.send_message(message.chat.id, 'Удалено')
    # после удаления свободного места возвращаемся в админ панель
    admin(message)

######### функция кнопки  удаление свободного места





######### функция кнопки  вернутся в главное меню
# функция кнопки вернутся в главное меню
@bot.message_handler(func=lambda message: message.text == 'Вернутся в главное меню')
def back(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Свободные места')
    keyboard.row('Записанные')
    keyboard.row('Добавить Свободные места')
    keyboard.row('Удалить Свободные места')
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard)
######### функция кнопки  вернутся в главное меню


############# функция кнопки изменить цену

# кнопка Изменить цену, проверяем что сообщение пришло от админа и выводим кнопки с именами услуг из базы nameprice
@bot.message_handler(func=lambda message: message.text == 'Изменить цену сервиса')
def change_price(message):
    cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        cursor.execute(f"SELECT servis FROM nameprice")
        nameprice = cursor.fetchall()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for name in nameprice:
            keyboard.row(name[0])
        keyboard.row('Назад')
        bot.send_message(message.chat.id, 'Выберите услугу', reply_markup=keyboard)
        bot.register_next_step_handler(message, change_price2)
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к админ панели')

# если нажата кнопка с именем услуги то выводим сообщение с ценой и запрашиваем новую цену
def change_price2(message):
    if message.text != 'Назад':
        # Получаем цену для выбранной услуги
        cursor.execute(f"SELECT price FROM nameprice WHERE servis = '{message.text}'")
        price = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f'Цена {price}')
        bot.send_message(message.chat.id, 'Введите новую цену')
        bot.register_next_step_handler(message, change_price3, message.text) # передаем название услуги в следующую функцию
    else:
        admin(message)


# если введенная цена не пустая и является числом то обновляем цену в базе данных и добавляем тнг к цене и выводим сообщение что цена обновлена и возвращаемся в админ панель
def change_price3(message, servis_name):
    if message.text != '' and message.text.isdigit():
        # Обновляем цену для выбранной услуги в базе данных nameprice и добавляем тнг к цене и выводим сообщение что цена обновлена
        cursor.execute(f"UPDATE nameprice SET price = '{message.text} тнг' WHERE servis = '{servis_name}'")
        conn.commit()
        bot.send_message(message.chat.id, 'Цена обновлена')
        # после обновления цены возвращаемся в админ панель
        admin(message)
    else:
        bot.send_message(message.chat.id, 'Неверный формат цены')
        # после обновления цены возвращаемся в админ панель
        admin(message)

################## функция кнопки изменить цену



# если нажата кнопка добавить админа то выводим сообщение с просьбой ввести id админа и запрашиваем id админа
@bot.message_handler(func=lambda message: message.text == 'Добавить Админа')
def add_admin(message):
    bot.send_message(message.chat.id, 'Введите id админа')
    bot.register_next_step_handler(message, add_admin2)

# если введенный id не пустой и является числом то добавляем админа в базу данных и выводим сообщение что админ добавлен и возвращаемся в админ панель
def add_admin2(message):
    if message.text != '' and message.text.isdigit():
        cursor.execute(f"INSERT INTO admin (admin_id) VALUES ({message.text})")
        conn.commit()
        bot.send_message(message.chat.id, 'Админ добавлен')
        # после добовление отпровляем сообщение админу что он добавлен в базу данных админов
        bot.send_message(message.text, 'Вы добавлены в базу данных админов')
        # после добавления админа возвращаемся в админ панель
        admin(message)
    else:
        bot.send_message(message.chat.id, 'Неверный формат id')
        # после добавления админа возвращаемся в админ панель
        admin(message)


# если нажата кнопка поменять приветствие Боту /start то выводим сообщение с просьбой ввести приветствие и запрашиваем приветствие и дальше меняем приветствие в базе данных message из ячейки message_start и выводим сообщение что приветствие обновлено и возвращаемся в админ панель
@bot.message_handler(func=lambda message: message.text == 'поменять приветствие Боту /start')
def change_message(message):
    # проверяем что сообщение пришло от админа
    cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        bot.send_message(message.chat.id, 'Введите приветствие')
        bot.register_next_step_handler(message, change_message2)
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к админ панели')

def change_message2(message):
    # Обновляем приветствие в базе данных message из ячейки message_start
    cursor.execute(f"UPDATE message SET message_start = '{message.text}'")
    conn.commit()
    bot.send_message(message.chat.id, 'Приветствие обновлено')
    # после обновления приветствия возвращаемся в админ панель
    admin(message)




# если нажата кнопка поменять сообщение, Дожидайтесь подтверждения то спрашиваем сообщение и дальше меняем сообщение в базе данных message из ячейки message_predoplata и выводим сообщение что сообщение обновлено и возвращаемся в админ панель
@bot.message_handler(func=lambda message: message.text == 'поменять сообщение, Дожидайтесь подтверждения записи')
def change_message2(message):
    # проверяем что сообщение пришло от админа
    cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        bot.send_message(message.chat.id, 'Введите сообщение')
        bot.register_next_step_handler(message, change_message3)
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к админ панели')

def change_message3(message):
    # Обновляем сообщение в базе данных message из ячейки message_predoplata
    cursor.execute(f"UPDATE message SET message_predoplata = '{message.text}'")
    conn.commit()
    bot.send_message(message.chat.id, 'Сообщение обновлено')
    # после обновления сообщения возвращаемся в админ панель
    admin(message)




# если нажата кнопка поменять имя Услуги  то выводим кнопки с  именами, после выбора сервиса выводим сообщение с просьбой ввести имя и запрашиваем имя и дальше меняем имя в базе данных nameprice из ячейки servis и выводим сообщение что имя обновлено и возвращаемся в админ панель
@bot.message_handler(func=lambda message: message.text == 'поменять имя Услуги')
def change_servis_name(message):
    # проверяем что сообщение пришло от админа
    cursor.execute(f"SELECT admin_id FROM admin WHERE admin_id = {message.from_user.id}")
    if cursor.fetchone() is not None:
        # выводим кнопки с именами услуг
        cursor.execute("SELECT servis FROM nameprice")
        servis_name = cursor.fetchall()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Назад')
        bot.send_message(message.chat.id, 'Назад', reply_markup=markup)

        for i in servis_name:
            markup.add(i[0])
        bot.send_message(message.chat.id, 'Выберите услугу', reply_markup=markup)
        bot.register_next_step_handler(message, change_servis_name2)
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к админ панели')

    if message.text == 'Назад':
        admin(message)


def change_servis_name2(message):
    # выводим сообщение с просьбой ввести имя и запрашиваем имя
    bot.send_message(message.chat.id, 'Введите имя')
    bot.register_next_step_handler(message, change_servis_name3, message.text)

def change_servis_name3(message, servis_name):
    # Обновляем имя в базе данных nameprice из ячейки servis
    cursor.execute(f"UPDATE nameprice SET servis = '{message.text}' WHERE servis = '{servis_name}'")
    conn.commit()
    bot.send_message(message.chat.id, 'Имя обновлено')
    # после обновления имени возвращаемся в админ панель
    admin(message)




while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)


