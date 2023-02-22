from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from datetime import datetime



engine = create_engine('sqlite:///database.db')
Base = declarative_base()
Base.metadata.create_all(bind=engine)





# определяем функцию для команды "/start"
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hello, world!")






# Описание модели таблицы
class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    date_time = Column(DateTime)
    service = Column(String)
    service_choice = Column(String)
    price = Column(Integer)
    is_admin = Column(Boolean)
    is_confirmed = Column(Boolean, default=False)

# Создание таблицы
Base.metadata.create_all(bind=engine)

from telegram import User

def is_admin(user_id):
    # Список id пользователей, которые являются администраторами
    admins = [123456789, 987654321]

    if user_id in admins:
        return True
    else:
        return False

def command_handler(update, context):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if is_admin(user.id):
        # Кнопки для админа
        respone - True
    else:
        # Кнопки для обычного пользователя
        respone = False


from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Appointment
from sqlalchemy.ext.declarative import declarative_base


def service_handler(update, context):
    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Получение списка всех уникальных названий услуг из базы данных
    services = session.query(Appointment.service).distinct()

    # Создание кнопок
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(service[0], callback_data=service[0])])

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Выберите услугу:', reply_markup=reply_markup)



def service_callback(update, context):
    query = update.callback_query
    service_name = query.data

    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Получение цены выбранной услуги
    appointment = session.query(Appointment).filter_by(service=service_name).first()
    price = appointment.price

    # Отправка цены и запрос на подтверждение
    message = f"Цена за {service_name}: {price}. Устраивает? (Да/Нет)"
    query.edit_message_text(text=message)

    # Сохранение выбора услуги в контексте
    context.user_data['service'] = service_name


def confirm_price_handler(update, context):
    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Получение списка свободных дат и времени для выбранной услуги
    service_name = context.user_data['service']
    appointments = session.query(Appointment).filter_by(service=service_name, is_confirmed=False)

    # Создание кнопок
    keyboard = []
    for appointment in appointments:
        keyboard.append([InlineKeyboardButton(str(appointment.date_time), callback_data=str(appointment.id))])

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Выберите свободное место:', reply_markup=reply_markup)


def appointment_callback(update, context):
    query = update.callback_query
    appointment_id = query.data

    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Получение объекта записи из базы данных
    appointment = session.query(Appointment).filter_by(id=appointment_id).first()

    # Сохранение имени и номера телефона пользователя в записи
    user = update.effective_user
    appointment.name = user.first_name
    appointment.phone = user.username

    # Подтверждение записи
    appointment.is_confirmed = True
    session.commit()

    # Создание кнопки для пользователя
    button_text = f"{appointment.service} ({appointment.price}) - {appointment.date_time}"
    button = InlineKeyboardButton(button_text, callback_data=appointment_id)
    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправка подтверждения и кнопки
    message = f"Запись успешно подтверждена:\n{appointment.service} ({appointment.price})\n{appointment.date_time}"
    query.edit_message_text(text=message, reply_markup=reply_markup)


def cancel_appointment_handler(update, context):
    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Получение объекта записи из базы данных
    appointment_id = context.user_data['appointment_id']
    appointment = session.query(Appointment).filter_by(id=appointment_id).first()

    # Удаление записи из базы данных
    session.delete(appointment)
    session.commit()

    # Отправка подтверждения
    message = "Запись успешно отменена"
    update.callback_query.edit_message_text(text=message)



def admin_handler(update, context):
    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Получение списка всех записей из базы данных
    appointments = session.query(Appointment).all()

    # Создание кнопок
    keyboard = []
    for appointment in appointments:
        button_text = f"{appointment.service} ({appointment.price}) - {appointment.date_time}"
        button = InlineKeyboardButton(button_text, callback_data=appointment.id)
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Выберите запись для редактирования:', reply_markup=reply_markup)




def edit_callback(update, context):
    query = update.callback_query
    appointment_id = query.data

    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Сохранение id записи в контексте
    context.user_data['appointment_id'] = appointment_id

    # Создание кнопок для редактирования записи
    buttons = [
        [InlineKeyboardButton('Редактировать дату и время', callback_data='edit_datetime')],
        [InlineKeyboardButton('Редактировать цену', callback_data='edit_price')],
        [InlineKeyboardButton('Удалить запись', callback_data='delete')],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    query.edit_message_reply_markup(reply_markup=reply_markup)


def edit_datetime_callback(update, context):
    query = update.callback_query

    # Отправка запроса на ввод новой даты и времени
    message = "Введите новую дату и время в формате 'гггг-мм-дд чч:мм':"
    query.edit_message_text(text=message)

    # Сохранение выбранного обработчика в контексте
    context.user_data['edit_callback'] = 'edit_datetime'


def edit_price_callback(update, context):
    query = update.callback_query

    # Отправка запроса на ввод новой цены
    message = "Введите новую цену:"
    query.edit_message_text(text=message)

    # Сохранение выбранного обработчика в контексте
    context.user_data['edit_callback'] = 'edit_price'


def edit_input_handler(update, context):
    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Получение объекта записи из базы данных
    appointment_id = context.user_data['appointment_id']
    appointment = session.query(Appointment).filter_by(id=appointment_id).first()

    # Редактирование записи
    edit_callback = context.user_data.get('edit_callback')
    if edit_callback == 'edit_datetime':
        appointment.date_time = datetime.strptime(update.message.text, '%Y-%m-%d %H:%M')
        message = "Дата и время успешно изменены"
    elif edit_callback == 'edit_price':
        appointment.price = update.message.text
        message = "Цена успешно изменена"
    session.commit()

    # Отправка подтверждения
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)



def delete_callback(update, context):
    query = update.callback_query

    # Создание объекта для работы с базой данных
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Получение объекта записи из базы данных
    appointment_id = context.user_data['appointment_id']
    appointment = session.query(Appointment).filter_by(id=appointment_id).first()

    # Удаление записи из базы данных
    session.delete(appointment)
    session.commit()

    # Отправка подтверждения
    message = "Запись успешно удалена"
    query.edit_message_text(text=message)




# создаем экземпляр Updater без аргументов
updater = Updater(use_context=True)

# создаем экземпляр Updater и передаем ему токен бота
updater = Updater(token='1911225697:AAG0PEEb4xTee0vgTWGlxW-UkbIQ0MD9fU0', use_context=True)

# добавляем обработчик для команды "/start"
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CallbackQueryHandler(edit_callback, pattern='^\\d+$'))
updater.dispatcher.add_handler(CallbackQueryHandler(edit_datetime_callback, pattern='edit_datetime'))
updater.dispatcher.add_handler(CallbackQueryHandler(edit_price_callback, pattern='edit_price'))
updater.dispatcher.add_handler(CallbackQueryHandler(delete_callback, pattern='delete'))
updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, edit_input_handler))


# запускаем бота
updater.start_polling()
updater.idle()
