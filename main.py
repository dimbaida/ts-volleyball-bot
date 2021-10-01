import telebot
import config
import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import scheduled_messages as sm
import db_commands as db


bot = telebot.TeleBot(config.bot_token)


@bot.message_handler(commands=['test'], chat_types=['private'])
def test(message):
    """
    Bot command for test purposes. Only available for the developers, telegram ids hardcoded
    If you're a collaborator, add your telegram id to 'developers' var in 'config.py'
    """
    if message.from_user.id in config.developers:
        pass


@bot.message_handler(commands=['send_reminder'], chat_types=['private'])
def send_reminder(message):
    """
    Manually send the reminder for upcoming event. Only available for the developers, telegram ids hardcoded
    If you're a collaborator, add your telegram id to 'developers' var in 'config.py'
    """
    if message.from_user.id in config.developers:
        telegram_ids = sm.send_event_reminder()
        bot.send_message(message.from_user.id,
                         f'Напоминание отправлено:<code>\n{telegram_ids}</code>',
                         reply_markup=telebot.types.ReplyKeyboardRemove(),
                         parse_mode='HTML',
                         disable_notification=True)


@bot.message_handler(commands=['get_id'], chat_types=['private'])
def get_id(message):
    bot.send_message(message.from_user.id,
                     f'<code>твой telegram ID: {message.from_user.id}</code>',
                     reply_markup=telebot.types.ReplyKeyboardRemove(),
                     parse_mode='HTML',
                     disable_notification=True)


@bot.message_handler(commands=['start'], chat_types=['private'])
def start(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn_01 = telebot.types.InlineKeyboardButton(f"Список событий", callback_data=f'LIST_EVENTS::')
    btn_02 = telebot.types.InlineKeyboardButton(f"Создать новое событие", callback_data=f'CREATE_EVENT::')
    keyboard.row(btn_01)
    if db.check_admin(message.chat.id):
        keyboard.row(btn_02)
    bot.send_message(message.chat.id,
                     '<code>Следующие события:</code>',
                     reply_markup=keyboard,
                     parse_mode='HTML',
                     disable_notification=True)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    try:
        command, data = call.data.split('::')

        if command == 'LIST_EVENTS':
            keyboard = telebot.types.InlineKeyboardMarkup()
            naming = {'train': '\U0001F3D0', 'game': '\U0001F3C5'}
            for event in db.upcoming_events():
                date_str = event[0].strftime('%d.%m.%Y')
                date = event[0]
                event_type = naming[event[1]]
                btn = telebot.types.InlineKeyboardButton(f"{event_type}  {date_str}", callback_data=f'EVENT::{date}')
                keyboard.row(btn)
            btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
            keyboard.row(btn_exit)
            bot.edit_message_text('<code>Следующие события:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'EVENT':
            date = data
            naming = {'train': '\U0001F3D0', 'game': '\U0001F3C5'}
            event_type = db.event_type_by_date(date)
            event_type = naming[event_type]
            date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'YES::{date}')
            btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'NO::{date}')
            btn_03 = telebot.types.InlineKeyboardButton('Список отметившихся', callback_data=f'LIST_PLAYERS::{date}')
            btn_04 = telebot.types.InlineKeyboardButton('Удалить', callback_data=f'DELETE_EVENT::{date}')
            btn_05 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
            keyboard.row(btn_01, btn_02)
            keyboard.row(btn_03)
            if db.check_admin(call.message.chat.id):
                keyboard.row(btn_04)
            keyboard.row(btn_05)
            bot.edit_message_text(f'{event_type}  <code>{date_str}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'YES':
            date = data
            date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            decision = db.check_attendance(call.message.chat.id, date)
            if decision == 'YES':
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{date}')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f'<code>Ты уже ранее был отмечен на {date_str}: YES</code>',
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)

            else:
                db.add_decision(call.message.chat.id, date, command)
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Вернуться к списку событий', callback_data=f'LIST_EVENTS::')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f'<code>Отмечено посещение {date_str}: YES</code>',
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)

                player = db.player_by_telegram_id(call.message.chat.id)
                bot.send_message(config.ts_bot_group_id,
                                 f"<code>{player[0]} {player[1]} отметил, что придет {date_str}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        if command == 'NO':
            date = data
            date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            decision = db.check_attendance(call.message.chat.id, date)
            if decision == 'NO':
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{date}')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f'<code>Ты уже ранее был отмечен на {date_str}: NO</code>',
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)
            else:
                db.add_decision(call.message.chat.id, date, command)
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Вернуться к списку событий', callback_data=f'LIST_EVENTS::')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f'<code>Отмечено посещение {date_str}: NO</code>',
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)
                player = db.player_by_telegram_id(call.message.chat.id)
                bot.send_message(config.ts_bot_group_id,
                                 f"<code>{player[0]} {player[1]} отметил, что пропустит {date_str}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        if command == 'LIST_PLAYERS':
            date = data
            date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{date}')
            keyboard.row(btn_01)
            players = db.event_players(date)
            bot.edit_message_text(f'<code>Список на {date_str}:\n\n{players}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'DELETE_EVENT':
            date = data
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_empty = telebot.types.InlineKeyboardButton(' ', callback_data='::')
            btn_01 = telebot.types.InlineKeyboardButton('Подтвердить', callback_data=f'DELETE_EVENT>>CONFIRMED::{date}')
            btn_02 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{date}')
            keyboard.row(btn_empty)
            keyboard.row(btn_empty, btn_01, btn_empty)
            keyboard.row(btn_empty)
            keyboard.row(btn_02)
            bot.edit_message_text(f'<code>УВЕРЕН? Все данные о событии будут стерты!</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'DELETE_EVENT>>CONFIRMED':
            date = data
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
            btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
            keyboard.row(btn_01)
            keyboard.row(btn_02)
            db.delete_event(date, telegram_id=call.message.chat.id)
            bot.edit_message_text(f'<code>Событие удалено</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'CREATE_EVENT':
            calendar, step = DetailedTelegramCalendar().build()
            bot.edit_message_text(f'Select {LSTEP[step]}',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=calendar)

        if command == 'CREATE_EVENT>>TYPE':
            naming = {'train': '\U0001F3D0', 'game': '\U0001F3C5'}
            date, event_type = data.split(':')
            date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
            btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
            keyboard.row(btn_01)
            keyboard.row(btn_02)
            db.create_event(date, event_type, telegram_id=call.message.chat.id)
            bot.edit_message_text(f'<code>Событие создано: {naming[event_type]} {date_str}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'EXIT':
            bot.delete_message(chat_id=call.message.chat.id,
                               message_id=call.message.message_id)

    except ValueError:  # This is due to telegram_bot_calendar can't handle custom callbacks

        date, key, step = DetailedTelegramCalendar().process(call.data)
        if not date and key:
            bot.edit_message_text(f"Select {LSTEP[step]}",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=key)
        elif date:
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Тренировка', callback_data=f'CREATE_EVENT>>TYPE::{date}:train')
            btn_02 = telebot.types.InlineKeyboardButton('Игра', callback_data=f'CREATE_EVENT>>TYPE::{date}:game')

            keyboard.row(btn_01, btn_02)
            bot.edit_message_text(f"<code>Выбери тип события на {date}</code>",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=keyboard,
                                  parse_mode='HTML')


if __name__ == '__main__':
    bot.polling(none_stop=True)
